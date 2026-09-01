<template>
  <div class="container token-detail">
    <div class="page-header">
      <div><router-link to="/scanner" class="back-link">← Back to scanner</router-link><div class="eyebrow">Market / Live token analysis</div><h1 class="page-title">{{ pair?.symbol || 'Token detail' }}</h1><p class="page-subtitle">OHLCV candles from the market data pipeline. No synthetic chart data is generated.</p></div>
      <div class="live-badge"><span class="status-dot live"></span> LIVE SYNC <small>{{ lastUpdated ? formatTime(lastUpdated) : 'Waiting' }}</small></div>
    </div>
    <div v-if="error" class="alert alert-danger">{{ error }}</div>
    <div class="metrics" v-if="chart"><div class="metric"><span>Trend</span><strong :class="trendClass">{{ chart.trend }}</strong></div><div class="metric"><span>Behavior</span><strong>{{ chart.behavior }}</strong></div><div class="metric"><span>RSI 14</span><strong>{{ chart.rsi ? chart.rsi.toFixed(1) : '-' }}</strong></div><div class="metric"><span>Volume ratio</span><strong>{{ chart.volume_ratio ? `${chart.volume_ratio.toFixed(2)}x` : '-' }}</strong></div><div class="metric"><span>Entry gate</span><strong :class="chart.entry_allowed ? 'positive' : 'negative'">{{ chart.entry_allowed ? 'OPEN' : 'BLOCKED' }}</strong></div></div>
    <div class="card chart-card"><div class="chart-toolbar"><div><div class="eyebrow">Price action</div><h2>Candlestick chart</h2></div><div class="timeframes"><button v-for="item in timeframes" :key="item.value" :class="{ active: timeframe === item.value }" @click="setTimeframe(item.value)">{{ item.label }}</button></div></div><div v-if="loading" class="loading"><div class="spinner"></div>Loading candle data...</div><CandleChart v-else :candles="candles" /><div class="legend"><span><i class="ema-fast"></i> EMA 9</span><span><i class="ema-slow"></i> EMA 21</span><span><i class="up"></i> Up candle</span><span><i class="down"></i> Down candle</span></div></div>
    <div class="card"><div class="section-heading"><div><div class="eyebrow">Signal context</div><h2>How the engine reads this chart</h2></div><span class="muted-label">{{ chart?.candle_count || candles.length }} CANDLES</span></div><ul class="reasons"><li v-for="reason in chart?.reasons || ['Waiting for enough candle history']" :key="reason">{{ reason }}</li></ul></div>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, onUnmounted, ref } from 'vue'
import { useRoute } from 'vue-router'
import { marketService } from '../services/api'
import CandleChart from '../components/CandleChart.vue'

const route = useRoute(); const pairId = String(route.params.pairId); const candles = ref<any[]>([]); const chart = ref<any>(null); const pair = ref<any>(null); const loading = ref(false); const error = ref(''); const timeframe = ref('minute'); const lastUpdated = ref(''); let timer: ReturnType<typeof setInterval> | undefined
const timeframes = [{ label: '1m', value: 'minute' }, { label: '5m', value: '5m' }, { label: '15m', value: '15m' }, { label: '1h', value: 'hour' }]
const trendClass = computed(() => chart.value?.trend === 'BULLISH' ? 'positive' : chart.value?.trend === 'BEARISH' ? 'negative' : '')
const formatTime = (value: string) => new Date(value).toLocaleTimeString()
const load = async () => { loading.value = !candles.value.length; error.value = ''; try { const [candleResponse, intelligenceResponse, pairsResponse] = await Promise.all([marketService.getCandles(pairId, timeframe.value, 100), marketService.getChartIntelligence(pairId, timeframe.value), marketService.getPairs(undefined, false)]); candles.value = candleResponse.data.items; chart.value = intelligenceResponse.data; lastUpdated.value = candleResponse.data.items.at(-1)?.timestamp || ''; pair.value = pairsResponse.data.find((item: any) => item.id === pairId) || pair.value } catch (err: any) { error.value = err.response?.data?.detail || 'Unable to load token chart' } finally { loading.value = false } }
const setTimeframe = async (value: string) => { timeframe.value = value; await load() }
onMounted(() => { load(); timer = setInterval(load, 15000) }); onUnmounted(() => clearInterval(timer))
</script>

<style scoped>
.back-link { display: inline-block; margin-bottom: 18px; color: var(--muted); font-size: .78rem; text-decoration: none; }.back-link:hover { color: var(--accent); }.live-badge { display: grid; grid-template-columns: auto auto; align-items: center; gap: 0 8px; color: var(--accent); font: .68rem 'DM Mono', monospace; }.live-badge small { grid-column: 2; color: var(--muted); }.metrics { display: grid; grid-template-columns: repeat(5, 1fr); gap: 10px; margin-bottom: 20px; }.metric { padding: 15px; background: var(--surface); border: 1px solid var(--line); border-radius: 12px; }.metric span { display: block; color: var(--muted); font-size: .68rem; }.metric strong { display: block; margin-top: 5px; font: 700 .95rem 'DM Mono', monospace; }.chart-toolbar { display: flex; align-items: center; justify-content: space-between; gap: 15px; margin-bottom: 18px; }.chart-toolbar h2 { margin: 4px 0 0; font-size: 1.15rem; }.timeframes { display: flex; gap: 4px; padding: 4px; background: var(--surface-raised); border-radius: 8px; }.timeframes button { padding: 7px 11px; border: 0; border-radius: 5px; background: transparent; color: var(--muted); font: .68rem 'DM Mono', monospace; }.timeframes button.active { background: var(--accent); color: #08100a; }.legend { display: flex; gap: 16px; flex-wrap: wrap; margin-top: 12px; color: var(--muted); font: .65rem 'DM Mono', monospace; }.legend span { display: flex; align-items: center; gap: 5px; }.legend i { display: inline-block; width: 12px; height: 3px; border-radius: 2px; }.ema-fast { background: var(--blue); }.ema-slow { background: var(--warning); }.up { background: var(--accent); }.down { background: var(--danger); }.reasons { display: grid; gap: 10px; margin: 0; padding: 0; list-style: none; }.reasons li { padding: 11px 13px; background: var(--surface-raised); border-radius: 8px; color: #ccd5e2; font-size: .78rem; }.reasons li::before { margin-right: 9px; color: var(--accent); content: '↗'; }
.token-detail :deep(.card) { min-width: 0; }.chart-card { min-width: 0; overflow: hidden; }.chart-card :deep(.candle-chart) { min-width: 0; }
@media (max-width: 760px) { .metrics { grid-template-columns: repeat(2, 1fr); }.chart-toolbar { display: block; }.timeframes { margin-top: 15px; width: fit-content; } }
</style>
