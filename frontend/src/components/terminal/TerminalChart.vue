<template>
  <div class="terminal-chart-wrap">
    <div v-if="loading" class="terminal-chart-state">Loading market structure...</div>
    <div v-else-if="!candles.length" class="terminal-chart-state"><span>◌</span><strong>No candle data yet</strong><small>Keep the pair watched until the next market collection.</small></div>
    <div v-else class="terminal-chart">
      <div class="chart-y-axis"><span>{{ formatPrice(maxPrice) }}</span><span>{{ formatPrice((maxPrice + minPrice) / 2) }}</span><span>{{ formatPrice(minPrice) }}</span></div>
      <div class="chart-grid"><i v-for="n in 5" :key="n"></i><div class="candle-area"><div v-for="(candle, index) in visibleCandles" :key="`${candle.timestamp}-${index}`" class="candle-slot"><span class="wick" :class="candle.close >= candle.open ? 'up' : 'down'" :style="wickStyle(candle)"></span><span class="body" :class="candle.close >= candle.open ? 'up' : 'down'" :style="bodyStyle(candle)"></span><span v-if="index === visibleCandles.length - 1" class="last-dot"></span></div></div><div class="volume-area"><span v-for="(candle, index) in visibleCandles" :key="`v-${index}`" :class="candle.close >= candle.open ? 'up' : 'down'" :style="volumeStyle(candle)"></span></div></div>
      <div class="chart-x-axis"><span>{{ formatTime(visibleCandles[0]?.timestamp) }}</span><span>{{ formatTime(visibleCandles[Math.floor(visibleCandles.length / 2)]?.timestamp) }}</span><span>{{ formatTime(visibleCandles[visibleCandles.length - 1]?.timestamp) }}</span></div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
interface Candle { timestamp: string; open: number; high: number; low: number; close: number; volume?: number }
const props = defineProps<{ candles: Candle[]; loading?: boolean }>()
const visibleCandles = computed(() => props.candles.slice(-72))
const maxPrice = computed(() => Math.max(...visibleCandles.value.map(c => Number(c.high)), 0))
const minPrice = computed(() => Math.min(...visibleCandles.value.map(c => Number(c.low)), 0))
const priceRange = computed(() => Math.max(maxPrice.value - minPrice.value, Number.EPSILON))
const percent = (value: number) => `${Math.max(0, Math.min(100, ((maxPrice.value - value) / priceRange.value) * 100))}%`
const wickStyle = (c: Candle) => ({ top: percent(c.high), height: `${Math.max(2, ((c.high - c.low) / priceRange.value) * 100)}%` })
const bodyStyle = (c: Candle) => ({ top: percent(Math.max(c.open, c.close)), height: `${Math.max(2, (Math.abs(c.close - c.open) / priceRange.value) * 100)}%` })
const volumeMax = computed(() => Math.max(...visibleCandles.value.map(c => Number(c.volume || 0)), 1))
const volumeStyle = (c: Candle) => ({ height: `${Math.max(4, (Number(c.volume || 0) / volumeMax.value) * 100)}%` })
const formatPrice = (value: number) => value < 0.001 ? value.toExponential(2) : value.toFixed(value < 1 ? 5 : 2)
const formatTime = (value?: string) => value ? new Date(value).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }) : '--'
</script>

<style scoped>
.terminal-chart-wrap{height:390px}.terminal-chart-state{display:grid;place-items:center;height:100%;align-content:center;gap:7px;color:var(--muted);font-size:.72rem;text-align:center}.terminal-chart-state span{font-size:2rem;color:var(--faint)}.terminal-chart-state strong{color:var(--text)}.terminal-chart-state small{font-size:.61rem}.terminal-chart{display:flex;height:100%;padding:5px 0 0 42px;position:relative}.chart-y-axis{position:absolute;left:0;top:7px;bottom:37px;display:flex;flex-direction:column;justify-content:space-between;color:var(--faint);font:500 .54rem 'DM Mono',monospace}.chart-grid{position:relative;flex:1;border-bottom:1px solid var(--line)}.chart-grid>i{display:block;height:20%;border-top:1px solid rgba(211,224,235,.06)}.candle-area{position:absolute;inset:0 0 74px;display:flex;align-items:stretch;gap:2px}.candle-slot{position:relative;flex:1;min-width:2px}.wick,.body{position:absolute;left:50%;display:block;transform:translateX(-50%)}.wick{width:1px}.body{width:min(9px,75%);min-height:2px;border-radius:1px}.up{background:var(--accent);box-shadow:0 0 6px rgba(0,245,139,.16)}.down{background:var(--danger)}.last-dot{position:absolute;top:15%;right:-2px;width:5px;height:5px;border-radius:50%;background:var(--accent);box-shadow:0 0 10px var(--accent)}.volume-area{position:absolute;right:0;bottom:0;left:0;display:flex;align-items:end;gap:2px;height:61px;border-top:1px solid rgba(211,224,235,.07)}.volume-area span{flex:1;min-width:2px;border-radius:2px 2px 0 0;opacity:.35}.chart-x-axis{position:absolute;right:0;bottom:0;left:42px;display:flex;justify-content:space-between;height:27px;padding-top:9px;color:var(--faint);font:500 .54rem 'DM Mono',monospace}
</style>
