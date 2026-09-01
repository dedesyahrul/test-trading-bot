<template>
  <div class="container dashboard-page">
    <div class="page-header">
      <div>
        <div class="eyebrow">MemeX / Command center</div>
        <h1 class="page-title">Market intelligence<br /><span>without the noise.</span></h1>
        <p class="page-subtitle">Monitor your autonomous trading system, validate strategies, and act on high-conviction signals.</p>
      </div>
      <div class="last-sync"><span class="status-dot" :class="{ live: wsConnected }"></span> {{ wsConnected ? 'Live data stream' : 'Waiting for stream' }}<small>Updated just now</small></div>
    </div>

    <div class="card system-banner">
      <div class="system-copy"><div class="eyebrow">System status</div><h2><span class="pulse" :class="botStatus"></span> {{ botStatus }}</h2><p>Trading mode: <strong>{{ tradingMode }}</strong> <span class="slash">/</span> {{ botStatus === 'STOPPED' ? 'Start the engine to begin monitoring' : 'Risk engine is monitoring' }}</p></div>
      <div class="banner-actions"><button @click="startBot" class="btn btn-success" :disabled="loading || botStatus === 'RUNNING'">Start engine</button><button @click="pauseBot" class="btn btn-secondary" :disabled="loading">Pause</button></div>
    </div>

    <div class="card">
      <div class="section-heading"><div><div class="eyebrow">Performance snapshot</div><h2>Today at a glance</h2></div><span class="date-chip">PAPER ACCOUNT</span></div>
      <div class="dashboard-grid">
        <div class="stat-card">
          <div class="stat-label">Bot Status</div>
          <div class="stat-value" :class="botStatus">{{ botStatus }}</div>
        </div>
        <div class="stat-card">
          <div class="stat-label">Trading Mode</div>
          <div class="stat-value">{{ tradingMode }}</div>
        </div>
        <div class="stat-card">
          <div class="stat-label">Active Positions</div>
          <div class="stat-value">{{ stats.openPositions }}</div>
        </div>
        <div class="stat-card">
          <div class="stat-label">Total PnL</div>
          <div class="stat-value" :class="pnlClass">${{ stats.totalPnl.toFixed(2) }}</div>
        </div>
        <div class="stat-card">
          <div class="stat-label">Win Rate</div>
          <div class="stat-value">{{ stats.winRate }}</div>
        </div>
        <div class="stat-card">
          <div class="stat-label">Signals (BUY)</div>
          <div class="stat-value">{{ stats.buySignals }}</div>
        </div>
        <div class="stat-card" v-if="systemStatus">
          <div class="stat-label">ML Model</div>
          <div class="stat-value" :class="systemStatus.integrations?.ml_model?.available ? 'positive' : ''">
            {{ systemStatus.integrations?.ml_model?.available ? 'Active' : 'Not Trained' }}
          </div>
        </div>
        <div class="stat-card" v-if="systemStatus">
          <div class="stat-label">Jupiter RPC</div>
          <div class="stat-value" :class="systemStatus.integrations?.jupiter_api?.rpc_healthy ? 'positive' : 'negative'">
            {{ systemStatus.integrations?.jupiter_api?.rpc_healthy ? 'OK' : 'Down' }}
          </div>
        </div>
      </div>
    </div>

    <div class="card" v-if="paperValidation">
      <div class="card-title">
        Paper Trading Validation ({{ paperValidation.period_days }} days)
        <span :class="['badge', paperValidation.ready_for_live ? 'badge-success' : 'badge-warning']">
          {{ paperValidation.ready_for_live ? 'READY' : 'IN PROGRESS' }}
        </span>
      </div>
      <p class="validation-rec">{{ paperValidation.recommendation }}</p>
      <div class="criteria-grid">
        <div
          v-for="(criterion, key) in paperValidation.validation_criteria"
          :key="key"
          :class="['criterion', criterion.passed ? 'passed' : 'failed']"
        >
          <span class="criterion-name">{{ formatCriterion(key) }}</span>
          <span>{{ criterion.actual }} / {{ criterion.required }}</span>
        </div>
      </div>
    </div>

    <div class="card chart-card">
      <div class="section-heading"><div><div class="eyebrow">Activity</div><h2>Daily volume</h2></div><span class="muted-label">LAST 7 DAYS</span></div>
      <PriceChart :data="chartData" label="Volume" color="#28a745" />
    </div>

    <div class="card controls-card">
      <div class="section-heading"><div><div class="eyebrow">Execution controls</div><h2>Manage engine</h2></div><span class="muted-label">USE WITH CARE</span></div>
      <div class="button-group">
        <button @click="startBot" class="btn btn-success" :disabled="loading">Start</button>
        <button @click="stopBot" class="btn btn-warning" :disabled="loading">Stop</button>
        <button @click="pauseBot" class="btn btn-info" :disabled="loading">Pause</button>
        <button @click="emergencyStop" class="btn btn-danger" :disabled="loading">Emergency Stop</button>
      </div>
      <div class="ws-status" :class="{ connected: wsConnected }">
        WebSocket: {{ wsConnected ? 'Connected' : 'Disconnected' }}
      </div>
      <p class="control-note">PAPER balance: ${{ paperBalance.toFixed(2) }}. A position opens only when a BUY signal passes risk, liquidity, and portfolio checks.</p>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted, watch } from 'vue'
import { botService, statisticsService, systemService } from '../services/api'
import { useWebSocketStore } from '../stores/websocket'
import { useToastStore } from '../stores/toast'
import PriceChart from '../components/PriceChart.vue'

const botStatus = ref('STOPPED')
const tradingMode = ref('PAPER')
const loading = ref(false)
const paperValidation = ref<any>(null)
const systemStatus = ref<any>(null)
const stats = ref({
  openPositions: 0,
  totalPnl: 0,
  winRate: '0%',
  buySignals: 0,
})
const chartData = ref<{ label: string; value: number }[]>([])
const paperBalance = ref(100)

const wsStore = useWebSocketStore()
const toast = useToastStore()
const wsConnected = computed(() => wsStore.isConnected)
const pnlClass = computed(() => (stats.value.totalPnl >= 0 ? 'positive' : 'negative'))

const formatCriterion = (key: string) => key.replace(/_/g, ' ')

const loadBotStatus = async () => {
  try {
    const response = await botService.getStatus()
    botStatus.value = response.data.state
    tradingMode.value = response.data.trading_mode
  } catch (err) {
    console.error('Error loading bot status:', err)
  }
}

const loadStatistics = async () => {
  try {
    const [summaryRes, dailyRes, validationRes] = await Promise.all([
      statisticsService.getSummary(),
      statisticsService.getDaily(7),
      statisticsService.getPaperValidation(),
    ])
    const summary = summaryRes.data
    stats.value = {
      openPositions: summary.positions?.open_count || 0,
      totalPnl: summary.pnl?.total || 0,
      winRate: summary.performance?.win_rate || '0%',
      buySignals: summary.signals?.buy_count || 0,
    }
    paperValidation.value = validationRes.data

    const daily = dailyRes.data.daily || {}
    chartData.value = Object.entries(daily).map(([day, data]: [string, any]) => ({
      label: day.slice(5),
      value: data.total_volume || 0,
    }))
  } catch (err) {
    console.error('Error loading statistics:', err)
  }
}

const loadSystemStatus = async () => {
  try {
    const res = await systemService.getStatus()
    systemStatus.value = res.data
    paperBalance.value = res.data.paper_initial_balance || 100
  } catch (err) {
    console.error('Error loading system status:', err)
  }
}

const startBot = async () => {
  loading.value = true
  try {
      await botService.start()
      await loadBotStatus()
      pollBotStatus()
      toast.success('Bot started')
  } catch (err) {
    toast.error('Failed to start bot')
  } finally {
    loading.value = false
  }
}

let statusPoll: ReturnType<typeof setInterval> | undefined
const pollBotStatus = () => {
  clearInterval(statusPoll)
  statusPoll = setInterval(async () => {
    await loadBotStatus()
    if (!['STARTING', 'STOPPING'].includes(botStatus.value)) clearInterval(statusPoll)
  }, 2000)
}

const stopBot = async () => {
  loading.value = true
  try {
    await botService.stop()
    await loadBotStatus()
    toast.info('Bot stopping...')
  } catch (err) {
    toast.error('Failed to stop bot')
  } finally {
    loading.value = false
  }
}

const pauseBot = async () => {
  loading.value = true
  try {
    await botService.pause()
    await loadBotStatus()
    toast.warning('Bot paused — monitoring only')
  } catch (err) {
    toast.error('Failed to pause bot')
  } finally {
    loading.value = false
  }
}

const emergencyStop = async () => {
  if (!confirm('Are you sure? This will stop all trading immediately.')) return
  loading.value = true
  try {
    await botService.emergencyStop()
    await loadBotStatus()
    toast.error('Emergency stop activated!')
  } catch (err) {
    toast.error('Emergency stop failed')
  } finally {
    loading.value = false
  }
}

const handleWsEvent = (topic: string, payload: any) => {
  if (topic === 'SIGNAL_GENERATED' && payload?.signal_type === 'BUY') {
    toast.info(`BUY signal: pair ${payload.pair_id?.slice(0, 8)}... (${(payload.confidence * 100).toFixed(0)}%)`)
  }
  if (topic === 'ORDER_STATUS_CHANGED') {
    const label = payload.type === 'BUY' ? 'Buy' : 'Sell'
    toast.success(`${label} order ${payload.status}`)
  }
  if (topic === 'POSITION_UPDATED') {
    const pnl = payload.pnl_usd
    if (pnl !== undefined) {
      const sign = pnl >= 0 ? '+' : ''
      toast.info(`Position update: ${sign}$${pnl.toFixed(2)}`)
    }
  }
  if (['POSITION_UPDATED', 'SIGNAL_GENERATED', 'ORDER_STATUS_CHANGED'].includes(topic)) {
    loadStatistics()
  }
  if (topic === 'ORDER_STATUS_CHANGED') loadBotStatus()
}

onMounted(() => {
  loadBotStatus()
  loadStatistics()
  loadSystemStatus()
  const wsUrl = import.meta.env.VITE_WS_URL || 'ws://localhost:17845/ws'
  wsStore.connect(wsUrl)
  wsStore.subscribe('POSITION_UPDATED')
  wsStore.subscribe('SIGNAL_GENERATED')
  wsStore.subscribe('ORDER_STATUS_CHANGED')
})

watch(
  () => wsStore.messages.length,
  () => {
    const last = wsStore.messages[wsStore.messages.length - 1]
    if (!last || last.type !== 'event') return
    handleWsEvent((last as any).topic, (last as any).payload)
  }
)

onUnmounted(() => {
  wsStore.disconnect()
  clearInterval(statusPoll)
})
</script>

<style scoped>
.page-title span { color: var(--accent); }
.last-sync { display: grid; grid-template-columns: auto auto; align-items: center; gap: 0 8px; color: var(--accent); font: .72rem 'DM Mono', monospace; text-transform: uppercase; }.last-sync small { grid-column: 2; color: var(--muted); font-size: .63rem; text-transform: none; }
.system-banner { display: flex; align-items: center; justify-content: space-between; padding: 28px 30px; background: linear-gradient(110deg, rgba(156,246,106,.12), rgba(16,21,31,.85) 45%); }.system-copy h2 { margin: 6px 0; font-size: 1.75rem; letter-spacing: -.04em; }.system-copy p { margin: 0; color: var(--muted); font-size: .78rem; }.system-copy strong { color: var(--text); }.slash { padding: 0 7px; color: var(--line); }.pulse, .status-dot { display: inline-block; width: 9px; height: 9px; border-radius: 50%; background: var(--danger); }.pulse.RUNNING, .pulse.live { background: var(--accent); box-shadow: 0 0 0 5px rgba(156,246,106,.12), 0 0 16px var(--accent); }.banner-actions { display: flex; gap: 9px; }.section-heading { display: flex; align-items: flex-start; justify-content: space-between; margin-bottom: 23px; }.section-heading h2 { margin: 5px 0 0; font-size: 1.2rem; letter-spacing: -.04em; }.date-chip, .muted-label { color: var(--muted); font: 500 .65rem 'DM Mono', monospace; letter-spacing: .1em; }.date-chip { padding: 6px 9px; border: 1px solid var(--line); border-radius: 5px; }.chart-card :deep(.chart-container) { height: 250px; }
.dashboard-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
  gap: 12px;
  margin-bottom: 1rem;
}

.stat-card {
  background: var(--surface-raised);
  padding: 18px;
  border-radius: 12px;
  border: 1px solid var(--line);
}

.stat-label {
  color: var(--muted);
  font-size: 0.72rem;
  margin-bottom: 0.5rem;
}

.stat-value {
  font-size: 1.55rem;
  font-weight: bold;
}

.stat-value.STOPPED { color: var(--danger); }
.stat-value.RUNNING { color: var(--accent); }
.stat-value.PAUSED { color: var(--warning); }
.stat-value.EMERGENCY_STOP { color: var(--danger); }
.stat-value.positive { color: var(--accent); }
.stat-value.negative { color: var(--danger); }

.button-group {
  display: flex;
  gap: 1rem;
  flex-wrap: wrap;
}

.btn-info { background-color: var(--blue); color: #08100a; }

.btn-info:hover { background-color: var(--blue); }

.ws-status {
  margin-top: 1rem;
  font-size: 0.875rem;
  color: var(--danger);
}

.ws-status.connected { color: var(--accent); }

.badge {
  font-size: 0.75rem;
  padding: 0.2rem 0.5rem;
  border-radius: 0.25rem;
  margin-left: 0.5rem;
}

.badge-success { background: rgba(156,246,106,.13); color: var(--accent); }
.badge-warning { background: rgba(255,200,87,.13); color: var(--warning); }

.validation-rec {
  color: var(--muted);
  margin-bottom: 1rem;
}

.criteria-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
  gap: 0.5rem;
}

.criterion {
  display: flex;
  justify-content: space-between;
  padding: 0.5rem 0.75rem;
  border-radius: 0.25rem;
  font-size: 0.875rem;
}

.criterion.passed { background: rgba(156,246,106,.08); border: 1px solid rgba(156,246,106,.35); }
.criterion.failed { background: rgba(255,109,125,.08); border: 1px solid rgba(255,109,125,.35); }

.criterion-name { text-transform: capitalize; }
.control-note { margin: 14px 0 0; color: var(--muted); font-size: .75rem; }
@media (max-width: 700px) { .system-banner { display: block; padding: 22px; }.banner-actions { margin-top: 20px; }.banner-actions .btn { flex: 1; }.last-sync { margin-top: 20px; } }
</style>
