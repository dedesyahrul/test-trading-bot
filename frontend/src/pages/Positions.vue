<template>
  <div class="container">
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
            <td>
              <button @click="closePosition(position.id)" class="btn btn-sm btn-danger">Close</button>
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
            <td>${{ position.exitPrice.toFixed(8) }}</td>
            <td :class="{ positive: position.pnl > 0, negative: position.pnl < 0 }">
              ${{ position.pnl.toFixed(2) }}
            </td>
            <td :class="{ positive: position.pnlPercent > 0, negative: position.pnlPercent < 0 }">
              {{ position.pnlPercent > 0 ? '+' : '' }}{{ (position.pnlPercent * 100).toFixed(2) }}%
            </td>
            <td>{{ position.duration }}</td>
            <td>{{ new Date(position.closedAt).toLocaleString() }}</td>
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
import { ref, computed, onMounted } from 'vue'
import { useWebSocketStore } from '../stores/websocket'
import { portfolioService } from '../services/api'

const wsStore = useWebSocketStore()
const openPositions = ref([])
const closedPositions = ref([])

const totalUnrealizedPnL = computed(() => {
  return openPositions.value.reduce((sum, p) => sum + p.pnl, 0)
})

const totalRealizedPnL = computed(() => {
  return closedPositions.value.reduce((sum, p) => sum + p.pnl, 0)
})

const totalEntryValue = computed(() => {
  return openPositions.value.reduce((sum, p) => sum + (p.entryPrice * p.amount), 0)
})

const totalCurrentValue = computed(() => {
  return openPositions.value.reduce((sum, p) => sum + (p.currentPrice * p.amount), 0)
})

const winRate = computed(() => {
  if (closedPositions.value.length === 0) return 0
  const wins = closedPositions.value.filter(p => p.pnl > 0).length
  return (wins / closedPositions.value.length) * 100
})

const loadPositions = async () => {
  try {
    const summary = await portfolioService.get('/portfolio/summary/wallet-id')
    // Parse positions from summary
    console.log('Positions loaded:', summary)
  } catch (error) {
    console.error('Error loading positions:', error)
  }
}

const closePosition = async (positionId: string) => {
  if (confirm('Are you sure you want to close this position?')) {
    try {
      console.log('Closing position:', positionId)
      // Call close position API
    } catch (error) {
      console.error('Error closing position:', error)
    }
  }
}

onMounted(() => {
  wsStore.connect()
  wsStore.subscribe('positions_update')
  loadPositions()
})
</script>

<style scoped>
.positions-summary {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 1rem;
  margin-bottom: 2rem;
}

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
