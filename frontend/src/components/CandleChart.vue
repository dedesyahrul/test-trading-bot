<template>
  <div class="candle-chart">
    <svg v-if="candles.length" class="chart-svg" viewBox="0 0 1000 420" preserveAspectRatio="none" role="img" aria-label="Candlestick chart">
      <g class="grid">
        <line v-for="line in gridLines" :key="line" x1="0" :y1="line" x2="1000" :y2="line" />
      </g>
      <g class="labels"><text v-for="label in priceLabels" :key="label.text" x="8" :y="label.y">{{ label.text }}</text></g>
      <g v-for="(candle, index) in visibleCandles" :key="`${candle.timestamp}-${index}`">
        <line :x1="x(index)" :y1="y(candle.high)" :x2="x(index)" :y2="y(candle.low)" :class="candle.close >= candle.open ? 'up' : 'down'" />
        <rect :x="x(index) - bodyWidth / 2" :y="Math.min(y(candle.open), y(candle.close))" :width="bodyWidth" :height="Math.max(2, Math.abs(y(candle.open) - y(candle.close)))" :class="candle.close >= candle.open ? 'up' : 'down'" />
        <rect class="volume" :x="x(index) - bodyWidth / 2" :y="390 - volumeHeight(candle.volume)" :width="bodyWidth" :height="volumeHeight(candle.volume)" />
      </g>
      <path v-if="fastEma.length" :d="linePath(fastEma)" class="ema-fast" />
      <path v-if="slowEma.length" :d="linePath(slowEma)" class="ema-slow" />
    </svg>
    <div v-else class="empty-chart"><strong>No OHLCV candles yet</strong><span>Provider may be rate-limited or this pair has no candle history.</span></div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'

interface Candle { timestamp: string; open: number; high: number; low: number; close: number; volume: number }
const props = defineProps<{ candles: Candle[] }>()
const visibleCandles = computed(() => props.candles.slice(-80))
const highs = computed(() => visibleCandles.value.map((c) => c.high))
const lows = computed(() => visibleCandles.value.map((c) => c.low))
const maxPrice = computed(() => Math.max(...highs.value, 0))
const minPrice = computed(() => Math.min(...lows.value, maxPrice.value || 1))
const priceRange = computed(() => maxPrice.value - minPrice.value || 1)
const maxVolume = computed(() => Math.max(...visibleCandles.value.map((c) => c.volume), 1))
const bodyWidth = computed(() => Math.max(3, 900 / Math.max(visibleCandles.value.length, 1) * .55))
const gridLines = [25, 135, 245, 355]
const x = (index: number) => 70 + (index + .5) * (880 / Math.max(visibleCandles.value.length, 1))
const y = (price: number) => 25 + (1 - (price - minPrice.value) / priceRange.value) * 330
const volumeHeight = (volume: number) => (volume / maxVolume.value) * 55
const priceLabels = computed(() => gridLines.map((line, index) => ({ y: line, text: (maxPrice.value - priceRange.value * index / 3).toPrecision(5) })))
const ema = (values: number[], period: number) => { if (values.length < period) return []; const result = Array<number>(period - 1).fill(NaN); let current = values.slice(0, period).reduce((a, b) => a + b, 0) / period; result.push(current); const multiplier = 2 / (period + 1); values.slice(period).forEach((value) => { current = (value - current) * multiplier + current; result.push(current) }); return result }
const fastEma = computed(() => ema(visibleCandles.value.map((c) => c.close), 9))
const slowEma = computed(() => ema(visibleCandles.value.map((c) => c.close), 21))
const linePath = (values: number[]) => values.map((value, index) => Number.isNaN(value) ? '' : `${index === 8 ? 'M' : 'L'} ${x(index)} ${y(value)}`).filter(Boolean).join(' ')
</script>

<style scoped>
.candle-chart { position: relative; width: 100%; max-width: 100%; height: clamp(260px, 42vw, 390px); overflow: hidden; }.chart-svg { display: block; width: 100%; height: 100%; overflow: hidden; background: linear-gradient(180deg, rgba(21,28,40,.55), rgba(16,21,31,.25)); }.grid line { stroke: rgba(152,171,197,.12); stroke-width: 1; vector-effect: non-scaling-stroke; }.labels text { fill: #8290a6; font: 12px 'DM Mono', monospace; }.up { stroke: #9cf66a; fill: #9cf66a; stroke-width: 1.2; vector-effect: non-scaling-stroke; }.down { stroke: #ff6d7d; fill: #ff6d7d; stroke-width: 1.2; vector-effect: non-scaling-stroke; }.volume { fill: #7ba7ff; opacity: .18; stroke: none; }.ema-fast, .ema-slow { fill: none; stroke-width: 2; vector-effect: non-scaling-stroke; }.ema-fast { stroke: #7ba7ff; }.ema-slow { stroke: #ffc857; }.empty-chart { position: absolute; inset: 0; display: grid; align-content: center; justify-items: center; gap: 7px; padding: 20px; color: #8290a6; font-size: .78rem; text-align: center; }.empty-chart strong { color: #f1f5fb; font-size: .95rem; }.empty-chart span { max-width: 320px; }
</style>
