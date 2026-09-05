<template>
  <div class="container dashboard-page">
    <div class="page-header dashboard-heading">
      <div><div class="eyebrow">Overview / {{ currentDate }}</div><h1 class="page-title">Good morning, trader<span class="title-dot">.</span></h1><p class="page-subtitle">Your autonomous edge is watching the market. Here is what needs your attention today.</p></div>
      <div class="header-utilities"><div class="last-sync"><span class="status-dot" :class="{ live: wsConnected }"></span>{{ wsConnected ? 'LIVE SYNC' : 'OFFLINE' }}<small>Last update just now</small></div><button @click="startBot" class="btn btn-success" :disabled="loading || botStatus === 'RUNNING'">{{ botStatus === 'RUNNING' ? 'Engine running' : 'Start engine' }}</button></div>
    </div>

    <div class="portfolio-hero card">
      <div class="portfolio-main"><div class="eyebrow">Total portfolio value <span class="eye">◉</span></div><div class="portfolio-value">${{ paperBalance.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 }) }}</div><div class="portfolio-change"><span>↗</span> ${{ Math.abs(stats.totalPnl).toFixed(2) }} <small>all-time PnL</small></div></div>
      <div class="hero-chart"><div class="chart-line"><span v-for="(point, index) in sparkline" :key="index" :style="{ height: `${point}%` }"></span></div><div class="chart-axis"><span>MON</span><span>TUE</span><span>WED</span><span>THU</span><span>FRI</span><span>SAT</span><span>SUN</span></div></div>
      <div class="hero-side"><div><span class="mini-label">Today</span><strong :class="pnlClass">{{ stats.totalPnl >= 0 ? '+' : '-' }}${{ Math.abs(stats.totalPnl).toFixed(2) }}</strong><small :class="pnlClass">{{ stats.totalPnl >= 0 ? '+2.84%' : '-2.84%' }}</small></div><div><span class="mini-label">Mode</span><strong>{{ tradingMode }}</strong><small class="live-copy"><span></span>{{ botStatus }}</small></div></div>
    </div>

    <div class="kpi-grid"><div class="kpi-card card"><span class="kpi-icon green">↗</span><div><span class="mini-label">Win rate</span><strong>{{ stats.winRate }}</strong><small class="positive">+4.2% vs last week</small></div></div><div class="kpi-card card"><span class="kpi-icon purple">⌁</span><div><span class="mini-label">Total trades</span><strong>{{ stats.buySignals }}</strong><small>Across all strategies</small></div></div><div class="kpi-card card"><span class="kpi-icon cyan">◌</span><div><span class="mini-label">Active positions</span><strong>{{ stats.openPositions }}</strong><small>Max 5 positions</small></div></div><div class="kpi-card card"><span class="kpi-icon orange">◈</span><div><span class="mini-label">Paper balance</span><strong>${{ paperBalance.toFixed(0) }}</strong><small>Available to deploy</small></div></div></div>

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

    <div class="content-grid">
      <div class="card chart-card"><div class="section-heading"><div><div class="eyebrow">Portfolio performance</div><h2>Account growth</h2></div><div class="time-tabs"><button v-for="period in ['1D','1W','1M','ALL']" :key="period" :class="{ active: selectedPeriod === period }" @click="selectedPeriod = period">{{ period }}</button></div></div><div class="chart-summary"><strong>${{ paperBalance.toLocaleString('en-US', { minimumFractionDigits: 2 }) }}</strong><span class="positive">+12.48% <small>this month</small></span></div><PriceChart :data="chartData" label="Portfolio" color="#00f58b" /></div>
      <div class="card activity-card"><div class="section-heading"><div><div class="eyebrow">Live feed</div><h2>Recent activity</h2></div><router-link to="/audit" class="view-all">View all →</router-link></div><div class="activity-list"><div class="activity-item"><span class="activity-symbol green-fill">↗</span><div><strong>Risk engine online</strong><small>All pre-trade gates active</small></div><time>Now</time></div><div class="activity-item"><span class="activity-symbol purple-fill">✦</span><div><strong>Scanner found 24 tokens</strong><small>3 passed initial liquidity filter</small></div><time>2m</time></div><div class="activity-item"><span class="activity-symbol cyan-fill">⌁</span><div><strong>Strategy heartbeat</strong><small>Momentum Scalper is watching</small></div><time>5m</time></div><div class="activity-item"><span class="activity-symbol orange-fill">!</span><div><strong>Paper mode protected</strong><small>Live trading remains disabled</small></div><time>12m</time></div></div></div>
    </div>

    <div class="bottom-grid"><div class="card performers-card"><div class="section-heading"><div><div class="eyebrow">Market pulse</div><h2>Top performers today</h2></div><router-link to="/scanner" class="view-all">Open scanner →</router-link></div><div class="token-list"><div v-for="token in performers" :key="token.symbol" class="token-row"><span class="token-avatar" :class="token.color">{{ token.symbol.slice(0,1) }}</span><div class="token-name"><strong>{{ token.symbol }}</strong><small>{{ token.pair }}</small></div><div class="token-price">{{ token.price }}</div><div class="token-change positive">{{ token.change }}</div><div class="safety"><span></span>{{ token.safety }}</div></div></div></div><div class="card bots-card"><div class="section-heading"><div><div class="eyebrow">Automation</div><h2>Active bots</h2></div><router-link to="/settings" class="view-all">Manage →</router-link></div><div class="bot-row"><span class="bot-status-dot"></span><div><strong>Momentum Scalper</strong><small>SOL / New launches</small></div><span class="bot-return positive">+8.42%</span></div><div class="bot-row"><span class="bot-status-dot idle"></span><div><strong>Liquidity Hunter</strong><small>Watching 18 pairs</small></div><span class="bot-state">Idle</span></div><button class="add-bot" @click="$router.push('/settings')">+ Create strategy</button></div></div>

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
const selectedPeriod = ref('1M')
const currentDate = new Date().toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' })
const sparkline = [44, 51, 47, 61, 58, 67, 64, 75, 72, 82, 78, 91]
const performers = [
  { symbol: 'BONK', pair: 'BONK / SOL', price: '$0.0000214', change: '+24.8%', safety: '94 / 100', color: 'orange-gradient' },
  { symbol: 'WIF', pair: 'WIF / SOL', price: '$2.148', change: '+18.6%', safety: '89 / 100', color: 'pink-gradient' },
  { symbol: 'POPCAT', pair: 'POPCAT / SOL', price: '$0.842', change: '+12.2%', safety: '86 / 100', color: 'blue-gradient' },
]

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
  const wsUrl = import.meta.env.VITE_WS_URL || `${location.protocol === 'https:' ? 'wss' : 'ws'}://${location.host}/ws`
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
.title-dot { color: var(--accent); }.header-utilities { display:flex;align-items:center;gap:20px }.last-sync { display: grid; grid-template-columns: auto auto; align-items: center; gap: 0 8px; color: var(--accent); font: .62rem 'DM Mono', monospace; text-transform: uppercase; }.last-sync small { grid-column: 2; color: var(--muted); font-size: .58rem; text-transform: none; }
.portfolio-hero { display:grid; grid-template-columns: 1.05fr 2fr .8fr; align-items:center; gap:32px; min-height:230px; padding:32px 34px; background: radial-gradient(circle at 45% 50%,rgba(0,245,139,.08),transparent 31%),linear-gradient(120deg,rgba(0,245,139,.06),rgba(17,20,25,.9) 52%); }.portfolio-value { margin:8px 0 8px; font-size:clamp(2.3rem,5vw,4.1rem); font-weight:800; letter-spacing:-.09em; line-height:1; }.portfolio-change { display:flex;align-items:center;gap:7px;color:var(--accent);font:500 .7rem 'DM Mono',monospace }.portfolio-change span{display:grid;width:22px;height:22px;place-items:center;border-radius:50%;background:var(--accent-soft);font-size:1rem}.portfolio-change small{color:var(--muted);font-family:'Manrope',sans-serif;font-size:.68rem}.hero-chart{align-self:end}.chart-line{display:flex;align-items:end;gap:8px;height:120px;padding:0 12px;border-bottom:1px solid var(--line);background:linear-gradient(180deg,rgba(0,245,139,.07),transparent)}.chart-line span{flex:1;min-width:5px;border-radius:5px 5px 0 0;background:linear-gradient(180deg,var(--accent),rgba(0,245,139,.14));box-shadow:0 0 13px rgba(0,245,139,.16);opacity:.85}.chart-axis{display:flex;justify-content:space-between;padding:8px 4px 0;color:var(--faint);font:500 .52rem 'DM Mono',monospace}.hero-side{display:grid;gap:25px;padding-left:24px;border-left:1px solid var(--line)}.hero-side strong{display:block;margin:5px 0;font-size:1.15rem;letter-spacing:-.04em}.hero-side small{display:block;color:var(--muted);font-size:.66rem}.mini-label{display:block;color:var(--faint);font:500 .57rem 'DM Mono',monospace;letter-spacing:.12em;text-transform:uppercase}.live-copy{color:var(--accent)!important;text-transform:uppercase}.live-copy span{display:inline-block;width:5px;height:5px;margin-right:5px;border-radius:50%;background:var(--accent);box-shadow:0 0 7px var(--accent)}
.kpi-grid{display:grid;grid-template-columns:repeat(4,1fr);gap:16px}.kpi-card{display:flex;align-items:center;gap:13px;margin:0;padding:19px}.kpi-icon{display:grid;width:35px;height:35px;place-items:center;border-radius:10px;font-size:1.2rem}.kpi-icon.green{background:var(--accent-soft);color:var(--accent)}.kpi-icon.purple{background:rgba(168,85,247,.12);color:#bd7bff}.kpi-icon.cyan{background:rgba(57,216,232,.11);color:var(--cyan)}.kpi-icon.orange{background:rgba(255,174,87,.12);color:#ffb65c}.kpi-card strong{display:block;margin:3px 0;font-size:1.3rem;letter-spacing:-.05em}.kpi-card small{display:block;color:var(--muted);font-size:.6rem}.content-grid{display:grid;grid-template-columns:1.65fr 1fr;gap:18px}.content-grid .card,.bottom-grid .card{margin:0}.chart-summary{display:flex;align-items:end;gap:12px;margin:-7px 0 6px}.chart-summary strong{font-size:1.75rem;letter-spacing:-.06em}.chart-summary span{font:500 .63rem 'DM Mono',monospace}.chart-summary small{color:var(--muted);font: .6rem 'Manrope',sans-serif}.chart-card :deep(.chart-container){height:270px}.time-tabs{display:flex;gap:3px}.time-tabs button{padding:5px 8px;border:0;border-radius:5px;background:transparent;color:var(--faint);font:500 .59rem 'DM Mono',monospace}.time-tabs button.active,.time-tabs button:hover{background:var(--accent-soft);color:var(--accent)}.view-all{color:var(--accent);font:500 .61rem 'DM Mono',monospace;text-decoration:none}.view-all:hover{text-decoration:underline}.activity-list{display:grid}.activity-item{display:flex;align-items:center;gap:11px;padding:12px 0;border-bottom:1px solid var(--line)}.activity-item:last-child{border-bottom:0}.activity-symbol{display:grid;width:27px;height:27px;place-items:center;border-radius:8px;font-weight:800}.green-fill{background:var(--accent-soft);color:var(--accent)}.purple-fill{background:rgba(168,85,247,.12);color:#bd7bff}.cyan-fill{background:rgba(57,216,232,.11);color:var(--cyan)}.orange-fill{background:rgba(255,174,87,.12);color:#ffb65c}.activity-item strong{display:block;font-size:.68rem}.activity-item small{display:block;color:var(--muted);font-size:.59rem}.activity-item time{margin-left:auto;color:var(--faint);font:500 .58rem 'DM Mono',monospace}.bottom-grid{display:grid;grid-template-columns:1.65fr 1fr;gap:18px}.token-list{display:grid}.token-row{display:grid;grid-template-columns:34px 1.4fr 1fr .7fr .7fr;align-items:center;gap:11px;padding:11px 0;border-top:1px solid var(--line)}.token-avatar{display:grid;width:30px;height:30px;place-items:center;border-radius:9px;color:white;font-size:.67rem;font-weight:800}.orange-gradient{background:linear-gradient(135deg,#ff9a3d,#eb563e)}.pink-gradient{background:linear-gradient(135deg,#ff6f9c,#ba47dd)}.blue-gradient{background:linear-gradient(135deg,#54b9ff,#5569ec)}.token-name strong,.token-name small{display:block}.token-name strong{font-size:.72rem}.token-name small{color:var(--muted);font-size:.58rem}.token-price{font:500 .66rem 'DM Mono',monospace}.token-change,.safety{font:500 .61rem 'DM Mono',monospace}.safety{color:var(--accent);text-align:right}.safety span{display:inline-block;width:5px;height:5px;margin-right:4px;border-radius:50%;background:var(--accent)}.bot-row{display:flex;align-items:center;gap:11px;padding:14px 0;border-bottom:1px solid var(--line)}.bot-row strong,.bot-row small{display:block}.bot-row strong{font-size:.72rem}.bot-row small{color:var(--muted);font-size:.6rem}.bot-status-dot{width:7px;height:7px;border-radius:50%;background:var(--accent);box-shadow:0 0 8px var(--accent)}.bot-status-dot.idle{background:var(--warning);box-shadow:none}.bot-return,.bot-state{margin-left:auto;font:500 .63rem 'DM Mono',monospace}.bot-state{color:var(--muted)}.add-bot{width:100%;margin-top:16px;padding:10px;border:1px dashed var(--line-strong);border-radius:8px;background:transparent;color:var(--muted);font-size:.67rem}.add-bot:hover{border-color:var(--accent);color:var(--accent)}
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
@media (max-width: 900px) { .portfolio-hero{grid-template-columns:1fr 1.3fr;}.hero-side{grid-column:1/-1;display:flex;justify-content:space-between;padding:18px 0 0;border-top:1px solid var(--line);border-left:0}.kpi-grid{grid-template-columns:repeat(2,1fr)}.content-grid,.bottom-grid{grid-template-columns:1fr} }
@media (max-width: 700px) { .dashboard-heading{margin-bottom:24px}.header-utilities{justify-content:space-between;margin-top:20px}.system-banner { display: block; padding: 22px; }.banner-actions { margin-top: 20px; }.banner-actions .btn { flex: 1; }.last-sync { margin-top: 0; }.portfolio-hero{display:block;padding:23px}.hero-chart{margin-top:28px}.hero-side{margin-top:25px}.kpi-grid{gap:10px}.kpi-card{padding:14px;gap:9px}.kpi-card strong{font-size:1.05rem}.kpi-card small{font-size:.53rem}.chart-card,.activity-card,.performers-card,.bots-card{overflow:hidden}.token-row{grid-template-columns:30px 1fr .8fr .7fr}.token-price{display:none}.safety{display:none}.controls-card{display:none} }
</style>
