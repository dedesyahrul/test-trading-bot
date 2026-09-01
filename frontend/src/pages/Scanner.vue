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
        <button @click="discoverTokens" class="btn btn-primary">Discover latest</button>
        <button @click="loadPage" class="btn btn-secondary">Sync</button>
        <select v-model="filterRisk" class="form-input">
          <option value="">All Risk Levels</option>
          <option value="LOW">Low Risk</option>
          <option value="MEDIUM">Medium Risk</option>
          <option value="HIGH">High Risk</option>
          <option value="CRITICAL">Critical Risk</option>
        </select>
        <select v-model="sortBy" class="form-input">
          <option value="updated_at">Recently updated</option>
          <option value="liquidity">Liquidity</option>
          <option value="price">Price</option>
          <option value="created_at">Newest pairs</option>
        </select>
      </div>

      <div class="loading" v-if="loading">
        <div class="spinner"></div>
        Loading tokens...
      </div>

      <table v-else-if="tokens.length > 0">
        <thead>
          <tr>
            <th>Token</th>
            <th>Price</th>
            <th>24h Change</th>
            <th>Volume</th>
            <th>Liquidity</th>
            <th>Risk</th>
            <th>Signal</th>
            <th>Updated</th>
            <th>Action</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="token in tokens" :key="token.id">
            <td><router-link :to="`/token/${token.id}`" class="token-link">{{ token.symbol }}</router-link></td>
            <td>${{ formatPrice(token.price) }}</td>
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
            <td class="updated-at">{{ token.marketDataAt ? new Date(token.marketDataAt).toLocaleTimeString() : 'No data' }}</td>
            <td>
              <button
                @click="toggleWatch(token)"
                :class="['btn btn-sm', token.isWatched ? 'btn-secondary' : 'btn-primary']"
                :disabled="updatingTokenId === token.id"
              >
                {{ updatingTokenId === token.id ? 'Saving...' : token.isWatched ? 'Unwatch' : 'Watch' }}
              </button>
            </td>
          </tr>
        </tbody>
      </table>

      <div v-else class="alert alert-info">
         {{ loadError || 'No tokens found matching your criteria.' }}
      </div>
      <div v-if="pages > 1" class="pagination">
        <button class="btn btn-secondary btn-sm" :disabled="page <= 1 || loading" @click="goToPage(page - 1)">Previous</button>
        <span>Page {{ page }} of {{ pages }} · {{ total }} pairs</span>
        <button class="btn btn-secondary btn-sm" :disabled="page >= pages || loading" @click="goToPage(page + 1)">Next</button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted, watch } from 'vue'
import { useWebSocketStore } from '../stores/websocket'
import { marketService } from '../services/api'
import { useToastStore } from '../stores/toast'

interface TokenRow {
  id: string
  symbol: string
  price: number
  change24h: number
  volume24h: number
  liquidity: number
  riskLevel: string
  signal: string
  isWatched: boolean
  marketDataAt?: string
}

const wsStore = useWebSocketStore()
const tokens = ref<TokenRow[]>([])
const loading = ref(false)
const searchQuery = ref('')
const filterRisk = ref('')
const updatingTokenId = ref<string | null>(null)
const toast = useToastStore()
const loadError = ref('')
const page = ref(1)
const pages = ref(0)
const total = ref(0)
const sortBy = ref('updated_at')
let liveTimer: ReturnType<typeof setInterval> | undefined

const formatPrice = (price: number) => {
  if (!price) return '0.00'
  return price < 0.01 ? price.toFixed(8) : price.toFixed(4)
}

const mapToken = (pair: any): TokenRow => ({
  id: pair.id,
  symbol: pair.symbol || `${pair.base_token}/${pair.quote_token}`,
  price: pair.price_usd || 0,
  change24h: pair.price_change_24h || 0,
  volume24h: pair.volume_24h_usd || 0,
  liquidity: pair.liquidity_usd || 0,
  riskLevel: pair.risk_level || 'UNKNOWN',
  signal: pair.signal_type || 'HOLD',
  isWatched: pair.is_watched || false,
  marketDataAt: pair.market_data_at,
})

const loadPage = async () => {
  loading.value = true
  loadError.value = ''
  try {
    const response = await marketService.getPairsPage({ page: page.value, page_size: 25, search: searchQuery.value || undefined, risk_level: filterRisk.value || undefined, sort_by: sortBy.value, sort_dir: 'desc' })
    tokens.value = response.data.items.map(mapToken)
    pages.value = response.data.pages
    total.value = response.data.total
    if (!tokens.value.length) loadError.value = 'No pairs match the current filters.'
  } catch (error: any) {
    console.error('Error loading tokens:', error)
    try {
      const fallback = await marketService.getPairs(undefined, false)
      tokens.value = fallback.data.map(mapToken)
      pages.value = 1
      total.value = tokens.value.length
      if (!tokens.value.length) loadError.value = 'No pairs are available yet. Check DexScreener connectivity and try again.'
    } catch (fallbackError) {
      console.error('Fallback load failed:', fallbackError)
      loadError.value = 'Unable to load tokens. DexScreener may be temporarily unavailable; try Refresh again.'
    }
  } finally {
    loading.value = false
  }
}

const discoverTokens = async () => {
  loading.value = true
  try {
    await marketService.discover()
    page.value = 1
    await loadPage()
  } catch (error: any) {
    loadError.value = error.response?.data?.detail || 'DexScreener discovery is temporarily unavailable.'
  } finally { loading.value = false }
}

const goToPage = async (nextPage: number) => { page.value = nextPage; await loadPage() }

watch([searchQuery, filterRisk, sortBy], async () => {
  page.value = 1
  await loadPage()
})

const toggleWatch = async (token: TokenRow) => {
  updatingTokenId.value = token.id
  try {
    if (token.isWatched) {
      await marketService.unwatchPair(token.id)
      token.isWatched = false
      toast.info(`${token.symbol} removed from watchlist`)
    } else {
      await marketService.watchPair(token.id)
      token.isWatched = true
      toast.success(`${token.symbol} added to watchlist`)
    }
  } catch (error: any) {
    console.error('Error updating watchlist:', error)
    toast.error(error.response?.data?.detail || 'Failed to update watchlist')
  } finally {
    updatingTokenId.value = null
  }
}

const getSignalClass = (signal: string) => {
  const classes: Record<string, string> = {
    BUY: 'success',
    SELL: 'danger',
    HOLD: 'warning',
    SKIP: 'secondary',
  }
  return classes[signal] || 'secondary'
}

const handleWsEvent = (topic: string, payload: any) => {
  if (topic === 'NEW_TOKEN_DISCOVERED') {
    loadPage()
    return
  }
  if (topic === 'MARKET_PRICE_UPDATED' && payload?.pair_id) {
    const token = tokens.value.find((t) => t.id === payload.pair_id)
    if (token) {
      if (payload.price_usd !== undefined) token.price = payload.price_usd
      if (payload.price_change_24h !== undefined) token.change24h = payload.price_change_24h
    }
  }
}

watch(
  () => wsStore.messages.length,
  () => {
    const last = wsStore.messages[wsStore.messages.length - 1]
    if (!last || last.type !== 'event') return
    handleWsEvent((last as any).topic, (last as any).payload)
  }
)

onMounted(() => {
  const wsUrl = import.meta.env.VITE_WS_URL || `${location.protocol === 'https:' ? 'wss' : 'ws'}://${location.host}/ws`
  wsStore.connect(wsUrl)
  wsStore.subscribe('NEW_TOKEN_DISCOVERED')
  wsStore.subscribe('MARKET_PRICE_UPDATED')
  loadPage()
  liveTimer = setInterval(loadPage, 15000)
})

onUnmounted(() => {
  wsStore.unsubscribe('NEW_TOKEN_DISCOVERED')
  wsStore.unsubscribe('MARKET_PRICE_UPDATED')
  clearInterval(liveTimer)
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

.badge-unknown {
  background-color: #6c757d;
  color: white;
  padding: 0.25rem 0.5rem;
  border-radius: 0.25rem;
}

.btn-sm {
  padding: 0.25rem 0.75rem;
  font-size: 0.875rem;
}
.pagination { display: flex; align-items: center; justify-content: center; gap: 16px; padding-top: 20px; color: var(--muted); font: .72rem 'DM Mono', monospace; }
.updated-at { color: var(--muted); font: .68rem 'DM Mono', monospace; }
.token-link { color: var(--text); font-weight: 800; text-decoration: none; }.token-link:hover { color: var(--accent); }
@media (max-width: 700px) { .pagination { gap: 8px; font-size: .62rem; } }
</style>
