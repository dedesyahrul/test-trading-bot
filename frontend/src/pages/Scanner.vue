<template>
  <div class="container">
    <div class="card">
      <div class="card-title">Token Scanner</div>
      <div class="scanner-controls">
        <input
          v-model="searchQuery"
          type="text"
          class="form-input"
          placeholder="Search tokens..."
        />
        <button @click="refreshTokens" class="btn btn-primary">Refresh</button>
        <select v-model="filterRisk" class="form-input">
          <option value="">All Risk Levels</option>
          <option value="LOW">Low Risk</option>
          <option value="MEDIUM">Medium Risk</option>
          <option value="HIGH">High Risk</option>
        </select>
      </div>

      <div class="loading" v-if="loading">
        <div class="spinner"></div>
        Loading tokens...
      </div>

      <table v-else>
        <thead>
          <tr>
            <th>Token</th>
            <th>Price</th>
            <th>24h Change</th>
            <th>Volume</th>
            <th>Liquidity</th>
            <th>Risk</th>
            <th>Signal</th>
            <th>Action</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="token in filteredTokens" :key="token.id">
            <td>{{ token.symbol }}</td>
            <td>${{ token.price }}</td>
            <td :class="{ positive: token.change24h > 0, negative: token.change24h < 0 }">
              {{ token.change24h > 0 ? '+' : '' }}{{ (token.change24h * 100).toFixed(2) }}%
            </td>
            <td>${{ (token.volume24h / 1000000).toFixed(2) }}M</td>
            <td>${{ (token.liquidity / 1000000).toFixed(2) }}M</td>
            <td><span :class="`badge-${token.riskLevel.toLowerCase()}`">{{ token.riskLevel }}</span></td>
            <td>
              <span :class="`badge badge-${getSignalClass(token.signal)}`">
                {{ token.signal }}
              </span>
            </td>
            <td>
              <button @click="watchToken(token.id)" class="btn btn-sm btn-primary">Watch</button>
            </td>
          </tr>
        </tbody>
      </table>

      <div v-if="tokens.length === 0 && !loading" class="alert alert-info">
        No tokens found matching your criteria.
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useWebSocketStore } from '../stores/websocket'
import { marketService } from '../services/api'

const wsStore = useWebSocketStore()
const tokens = ref([])
const loading = ref(false)
const searchQuery = ref('')
const filterRisk = ref('')

const filteredTokens = computed(() => {
  return tokens.value
    .filter(t => {
      const matchesSearch = t.symbol.toLowerCase().includes(searchQuery.value.toLowerCase())
      const matchesRisk = !filterRisk.value || t.riskLevel === filterRisk.value
      return matchesSearch && matchesRisk
    })
    .sort((a, b) => {
      // Sort by signal strength and risk
      const signalOrder = { BUY: 0, SELL: 1, HOLD: 2, SKIP: 3 }
      return (signalOrder[a.signal] || 3) - (signalOrder[b.signal] || 3)
    })
})

const refreshTokens = async () => {
  loading.value = true
  try {
    const response = await marketService.getPairs(undefined, true)
    tokens.value = response.data.map(pair => ({
      id: pair.id,
      symbol: `${pair.base_token}/${pair.quote_token}`,
      price: pair.price_usd,
      change24h: pair.price_change_24h || 0,
      volume24h: pair.volume_24h_usd || 0,
      liquidity: pair.liquidity_usd || 0,
      riskLevel: pair.risk_level || 'UNKNOWN',
      signal: pair.signal_type || 'HOLD',
    }))
  } catch (error) {
    console.error('Error loading tokens:', error)
  } finally {
    loading.value = false
  }
}

const watchToken = async (tokenId: string) => {
  try {
    await marketService.watchPair(tokenId)
    console.log('Token watched')
  } catch (error) {
    console.error('Error watching token:', error)
  }
}

const getSignalClass = (signal: string) => {
  const classes = {
    BUY: 'success',
    SELL: 'danger',
    HOLD: 'warning',
    SKIP: 'secondary',
  }
  return classes[signal] || 'secondary'
}

onMounted(() => {
  // Connect WebSocket and subscribe to market updates
  wsStore.connect()
  wsStore.subscribe('market_updates')
  refreshTokens()
})
</script>

<style scoped>
.scanner-controls {
  display: flex;
  gap: 1rem;
  margin-bottom: 1.5rem;
  flex-wrap: wrap;
}

.scanner-controls input,
.scanner-controls select,
.scanner-controls button {
  flex: 1;
  min-width: 150px;
}

.positive {
  color: #28a745;
}

.negative {
  color: #dc3545;
}

.badge-low {
  background-color: #28a745;
  color: white;
  padding: 0.25rem 0.5rem;
  border-radius: 0.25rem;
}

.badge-medium {
  background-color: #ffc107;
  color: black;
  padding: 0.25rem 0.5rem;
  border-radius: 0.25rem;
}

.badge-high {
  background-color: #fd7e14;
  color: white;
  padding: 0.25rem 0.5rem;
  border-radius: 0.25rem;
}

.badge-critical {
  background-color: #dc3545;
  color: white;
  padding: 0.25rem 0.5rem;
  border-radius: 0.25rem;
}

.btn-sm {
  padding: 0.25rem 0.75rem;
  font-size: 0.875rem;
}
</style>
