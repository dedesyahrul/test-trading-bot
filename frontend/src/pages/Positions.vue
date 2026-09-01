<template>
  <div class="container">
    <div class="page-header">
      <div>
        <div class="eyebrow">Portfolio / Live monitoring</div>
        <h1 class="page-title">Positions</h1>
        <p class="page-subtitle">Prices refresh automatically every 10 seconds. The timestamp below shows the latest market snapshot received for each pair.</p>
      </div>
      <div class="live-refresh"><span class="status-dot live"></span> AUTO REFRESH 10S</div>
    </div>
    <div class="card">
      <div class="card-title">Open Positions</div>
      
      <div class="positions-summary">
        <div class="stat-card">
          <div class="stat-label">Total Open Positions</div>
          <div class="stat-value">{{ openPositions.length }}</div>
        </div>
        <div class="stat-card">
          <div class="stat-label">Unrealized PnL</div>
          <div class="stat-value" :class="{ positive: totalUnrealizedPnL > 0, negative: totalUnrealizedPnL < 0 }">
            ${{ totalUnrealizedPnL.toFixed(2) }}
          </div>
        </div>
        <div class="stat-card">
          <div class="stat-label">Total Entry Value</div>
          <div class="stat-value">${{ totalEntryValue.toFixed(2) }}</div>
        </div>
        <div class="stat-card">
          <div class="stat-label">Total Current Value</div>
          <div class="stat-value">${{ totalCurrentValue.toFixed(2) }}</div>
        </div>
      </div>

      <table v-if="openPositions.length > 0">
        <thead>
          <tr>
            <th>Token</th>
            <th>Entry Price</th>
            <th>Current Price</th>
            <th>Amount</th>
            <th>Entry Value</th>
            <th>Current Value</th>
            <th>PnL</th>
            <th>PnL %</th>
            <th>TP/SL</th>
            <th>Market data</th>
            <th>Action</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="position in openPositions" :key="position.id">
            <td><strong>{{ position.symbol }}</strong></td>
            <td>${{ position.entryPrice.toFixed(8) }}</td>
            <td>${{ position.currentPrice.toFixed(8) }}</td>
            <td>{{ position.amount.toFixed(6) }}</td>
            <td>${{ (position.entryPrice * position.amount).toFixed(2) }}</td>
            <td>${{ (position.currentPrice * position.amount).toFixed(2) }}</td>
            <td :class="{ positive: position.pnl > 0, negative: position.pnl < 0 }">
              ${{ position.pnl.toFixed(2) }}
            </td>
            <td :class="{ positive: position.pnlPercent > 0, negative: position.pnlPercent < 0 }">
              {{ position.pnlPercent > 0 ? '+' : '' }}{{ (position.pnlPercent * 100).toFixed(2) }}%
            </td>
            <td>
              <div class="tp-sl">
                <span v-if="position.takeProfit">TP: ${{ position.takeProfit.toFixed(8) }}</span>
                <span v-if="position.stopLoss">SL: ${{ position.stopLoss.toFixed(8) }}</span>
              </div>
            </td>
            <td class="market-time">{{ position.marketDataAt ? new Date(position.marketDataAt).toLocaleTimeString() : 'No data' }}</td>
            <td>
              <button @click="closePosition(position.id)" class="btn btn-sm btn-danger" :disabled="closing">
                Close
              </button>
            </td>
          </tr>
        </tbody>
      </table>

      <div v-else class="alert alert-info">
        No open positions.
      </div>
    </div>

    <div class="card">
      <div class="card-title">Closed Positions</div>
      
      <div class="positions-summary">
        <div class="stat-card">
          <div class="stat-label">Total Closed Positions</div>
          <div class="stat-value">{{ closedPositions.length }}</div>
        </div>
        <div class="stat-card">
          <div class="stat-label">Realized PnL</div>
          <div class="stat-value" :class="{ positive: totalRealizedPnL > 0, negative: totalRealizedPnL < 0 }">
            ${{ totalRealizedPnL.toFixed(2) }}
          </div>
        </div>
        <div class="stat-card">
          <div class="stat-label">Win Rate</div>
          <div class="stat-value">{{ winRate.toFixed(2) }}%</div>
        </div>
      </div>

      <table v-if="closedPositions.length > 0">
        <thead>
          <tr>
            <th>Token</th>
            <th>Entry Price</th>
            <th>Exit Price</th>
            <th>PnL</th>
            <th>PnL %</th>
            <th>Duration</th>
            <th>Closed At</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="position in closedPositions" :key="position.id">
            <td><strong>{{ position.symbol }}</strong></td>
            <td>${{ position.entryPrice.toFixed(8) }}</td>
            <td>${{ (position.exitPrice || 0).toFixed(8) }}</td>
            <td :class="{ positive: position.pnl > 0, negative: position.pnl < 0 }">
              ${{ position.pnl.toFixed(2) }}
            </td>
            <td :class="{ positive: position.pnlPercent > 0, negative: position.pnlPercent < 0 }">
              {{ position.pnlPercent > 0 ? '+' : '' }}{{ (position.pnlPercent * 100).toFixed(2) }}%
            </td>
            <td>{{ position.duration || '-' }}</td>
            <td>{{ position.closedAt ? new Date(position.closedAt).toLocaleString() : '-' }}</td>
          </tr>
        </tbody>
      </table>

      <div v-else class="alert alert-info">
        No closed positions.
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted, watch } from 'vue'
import { useWebSocketStore } from '../stores/websocket'
import { portfolioService } from '../services/api'

interface PositionRow {
  id: string
  symbol: string
  entryPrice: number
  currentPrice: number
  exitPrice?: number
  amount: number
  pnl: number
  pnlPercent: number
  takeProfit?: number
  stopLoss?: number
  duration?: string
  closedAt?: string
  marketDataAt?: string
  exitReason?: string
  exitPressure?: number
  highestPrice?: number
  maeUsd?: number
  mfeUsd?: number
}

const wsStore = useWebSocketStore()
const openPositions = ref<PositionRow[]>([])
const closedPositions = ref<PositionRow[]>([])
const closing = ref(false)
const walletId = ref<string | null>(null)
let refreshTimer: ReturnType<typeof setInterval> | undefined

const mapPosition = (p: any): PositionRow => ({
  id: p.id,
  symbol: p.symbol,
  entryPrice: p.entry_price,
  currentPrice: p.current_price || p.entry_price,
  exitPrice: p.exit_price,
  amount: p.entry_amount,
  pnl: p.pnl,
  pnlPercent: p.pnl_percent,
  takeProfit: p.take_profit,
  stopLoss: p.stop_loss,
  duration: p.duration,
  closedAt: p.closed_at,
  marketDataAt: p.market_data_at,
  exitReason: p.exit_reason,
  exitPressure: p.exit_pressure,
  highestPrice: p.highest_price,
  maeUsd: p.mae_usd,
  mfeUsd: p.mfe_usd,
})

const totalUnrealizedPnL = computed(() =>
  openPositions.value.reduce((sum, p) => sum + p.pnl, 0)
)
const totalRealizedPnL = computed(() =>
  closedPositions.value.reduce((sum, p) => sum + p.pnl, 0)
)
const totalEntryValue = computed(() =>
  openPositions.value.reduce((sum, p) => sum + p.entryPrice * p.amount, 0)
)
const totalCurrentValue = computed(() =>
  openPositions.value.reduce((sum, p) => sum + p.currentPrice * p.amount, 0)
)
const winRate = computed(() => {
  if (closedPositions.value.length === 0) return 0
  const wins = closedPositions.value.filter((p) => p.pnl > 0).length
  return (wins / closedPositions.value.length) * 100
})

const loadPositions = async () => {
  try {
    if (!walletId.value) {
      const walletRes = await portfolioService.getDefaultWallet()
      walletId.value = walletRes.data.id
    }
    const [openRes, closedRes] = await Promise.all([
      portfolioService.listPositions('OPEN', walletId.value || undefined),
      portfolioService.listPositions('CLOSED', walletId.value || undefined),
    ])
    openPositions.value = (openRes.data.positions || []).map(mapPosition)
    closedPositions.value = (closedRes.data.positions || []).map(mapPosition)
  } catch (error) {
    console.error('Error loading positions:', error)
  }
}

const closePosition = async (positionId: string) => {
  if (!confirm('Are you sure you want to close this position?')) return
  closing.value = true
  try {
    await portfolioService.closePosition(positionId)
    await loadPositions()
  } catch (error) {
    console.error('Error closing position:', error)
    alert('Failed to close position')
  } finally {
    closing.value = false
  }
}

watch(
  () => wsStore.messages.length,
  () => {
    const last = wsStore.messages[wsStore.messages.length - 1]
    if (!last || last.type !== 'event') return
    const topic = (last as any).topic
    if (topic === 'POSITION_UPDATED' || topic === 'ORDER_STATUS_CHANGED') {
      loadPositions()
    }
  }
)

onMounted(() => {
  const wsUrl = import.meta.env.VITE_WS_URL || `${location.protocol === 'https:' ? 'wss' : 'ws'}://${location.host}/ws`
  wsStore.connect(wsUrl)
  wsStore.subscribe('POSITION_UPDATED')
  wsStore.subscribe('ORDER_STATUS_CHANGED')
  loadPositions()
  refreshTimer = setInterval(loadPositions, 10000)
})

onUnmounted(() => {
  wsStore.unsubscribe('POSITION_UPDATED')
  wsStore.unsubscribe('ORDER_STATUS_CHANGED')
  clearInterval(refreshTimer)
})
</script>

<style scoped>
.positions-summary {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 1rem;
  margin-bottom: 2rem;
}
.live-refresh { color: var(--accent); font: .68rem 'DM Mono', monospace; }.market-time { color: var(--muted); font: .68rem 'DM Mono', monospace; }

.positive {
  color: #28a745;
}

.negative {
  color: #dc3545;
}

.tp-sl {
  display: flex;
  flex-direction: column;
  gap: 0.25rem;
  font-size: 0.875rem;
}

.btn-sm {
  padding: 0.25rem 0.75rem;
  font-size: 0.875rem;
}
</style>
