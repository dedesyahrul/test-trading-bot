<template>
  <div class="container">
    <div class="page-header">
      <div><div class="eyebrow">Research / Watchlist</div><h1 class="page-title">Watch history</h1><p class="page-subtitle">See every token you added or removed from monitoring, including its latest available market snapshot.</p></div>
      <button class="btn btn-secondary" @click="loadHistory" :disabled="loading">{{ loading ? 'Syncing...' : 'Sync history' }}</button>
    </div>
    <div class="card">
      <div class="filters"><input v-model="search" class="form-input" placeholder="Search token symbol" @keyup.enter="applyFilters" /><select v-model="action" class="form-input"><option value="">All actions</option><option value="WATCH_PAIR">Added to watchlist</option><option value="UNWATCH_PAIR">Removed from watchlist</option></select><button class="btn btn-primary" @click="applyFilters">Apply</button></div>
      <div v-if="loading" class="loading"><div class="spinner"></div>Loading watch history...</div>
      <div v-else-if="error" class="alert alert-danger">{{ error }}</div>
      <div v-else-if="!items.length" class="alert">No watchlist history found.</div>
      <div v-else class="history-list">
        <article v-for="item in items" :key="item.id" class="history-row"><div class="token-icon">{{ item.symbol.slice(0, 1) }}</div><div class="token-main"><strong>{{ item.symbol }}</strong><small>{{ item.pair_id }}</small></div><div class="market-stat"><span>Price</span><strong>{{ item.price_usd ? `$${formatPrice(item.price_usd)}` : '-' }}</strong></div><div class="market-stat"><span>Liquidity</span><strong>{{ item.liquidity_usd ? `$${(item.liquidity_usd / 1000).toFixed(1)}K` : '-' }}</strong></div><div class="history-action"><span :class="['badge', item.is_watched ? 'badge-success' : 'badge-danger']">{{ item.is_watched ? 'WATCHED' : 'UNWATCHED' }}</span><small>{{ formatDate(item.created_at) }}</small><button v-if="item.is_watched" class="btn btn-secondary btn-sm unwatch-button" :disabled="unwatchingId === item.pair_id" @click="unwatch(item)">{{ unwatchingId === item.pair_id ? 'Saving...' : 'Unwatch' }}</button></div></article>
      </div>
      <div v-if="pages > 1" class="pagination"><button class="btn btn-secondary btn-sm" :disabled="page <= 1 || loading" @click="goToPage(page - 1)">Previous</button><span>Page {{ page }} of {{ pages }} · {{ total }} events</span><button class="btn btn-secondary btn-sm" :disabled="page >= pages || loading" @click="goToPage(page + 1)">Next</button></div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { marketService, watchlistService } from '../services/api'
import { useToastStore } from '../stores/toast'
interface HistoryItem { id: string; pair_id: string; symbol: string; action: string; is_watched: boolean; price_usd?: number; liquidity_usd?: number; created_at: string }
const items = ref<HistoryItem[]>([]); const loading = ref(false); const error = ref(''); const search = ref(''); const action = ref(''); const page = ref(1); const pages = ref(0); const total = ref(0); const unwatchingId = ref<string | null>(null); const toast = useToastStore()
const formatDate = (value: string) => new Date(value).toLocaleString(); const formatPrice = (value: number) => value < 0.01 ? value.toFixed(8) : value.toFixed(4)
const loadHistory = async () => { loading.value = true; error.value = ''; try { const response = await watchlistService.history({ page: page.value, page_size: 25, search: search.value || undefined, action: action.value || undefined }); items.value = response.data.items; pages.value = response.data.pages; total.value = response.data.total } catch (err: any) { error.value = err.response?.data?.detail || 'Failed to load watchlist history' } finally { loading.value = false } }
const applyFilters = () => { page.value = 1; loadHistory() }; const goToPage = (next: number) => { page.value = next; loadHistory() }
const unwatch = async (item: HistoryItem) => { unwatchingId.value = item.pair_id; try { await marketService.unwatchPair(item.pair_id); item.is_watched = false; toast.info(`${item.symbol} removed from watchlist`) } catch (err: any) { toast.error(err.response?.data?.detail || 'Failed to unwatch pair') } finally { unwatchingId.value = null } }
onMounted(loadHistory)
</script>

<style scoped>
.filters { display: grid; grid-template-columns: 1fr 1fr auto; gap: 10px; margin-bottom: 20px; }.history-list { display: grid; gap: 8px; }.history-row { display: grid; grid-template-columns: 36px minmax(180px, 1fr) 120px 140px 180px; align-items: center; gap: 16px; padding: 15px; background: var(--surface-raised); border: 1px solid var(--line); border-radius: 12px; }.token-icon { display: grid; width: 34px; height: 34px; place-items: center; border-radius: 10px; background: rgba(156,246,106,.12); color: var(--accent); font-weight: 800; }.token-main strong, .token-main small, .history-action small, .market-stat span, .market-stat strong { display: block; }.token-main small, .history-action small { overflow: hidden; margin-top: 3px; color: var(--muted); font: .62rem 'DM Mono', monospace; text-overflow: ellipsis; white-space: nowrap; }.market-stat span { color: var(--muted); font-size: .65rem; }.market-stat strong { margin-top: 3px; font: .8rem 'DM Mono', monospace; }.history-action { text-align: right; }.history-action small { margin-top: 6px; }.unwatch-button { margin-top: 8px; }.pagination { display: flex; justify-content: center; align-items: center; gap: 16px; padding-top: 20px; color: var(--muted); font: .7rem 'DM Mono', monospace; }
@media (max-width: 760px) { .filters { grid-template-columns: 1fr; }.history-row { grid-template-columns: 34px 1fr auto; gap: 10px; }.market-stat { display: none; }.history-action { text-align: right; } }
</style>
