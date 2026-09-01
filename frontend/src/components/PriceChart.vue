<template>
  <div class="chart-container">
    <canvas ref="chartCanvas"></canvas>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted, watch } from 'vue'
import {
  Chart,
  LineController,
  LineElement,
  PointElement,
  LinearScale,
  TimeScale,
  CategoryScale,
  Tooltip,
  Legend,
  Filler,
} from 'chart.js'

Chart.register(
  LineController,
  LineElement,
  PointElement,
  LinearScale,
  TimeScale,
  CategoryScale,
  Tooltip,
  Legend,
  Filler,
)

interface DataPoint {
  label: string
  value: number
}

const props = defineProps<{
  data: DataPoint[]
  label?: string
  color?: string
}>()

const chartCanvas = ref<HTMLCanvasElement | null>(null)
let chart: Chart | null = null

const renderChart = () => {
  if (!chartCanvas.value) return

  if (chart) {
    chart.destroy()
  }

   const color = props.color || '#9cf66a'

  chart = new Chart(chartCanvas.value, {
    type: 'line',
    data: {
      labels: props.data.map((d) => d.label),
      datasets: [
        {
          label: props.label || 'Price',
          data: props.data.map((d) => d.value),
          borderColor: color,
          backgroundColor: color + '20',
          fill: true,
          tension: 0.3,
          pointRadius: 2,
        },
      ],
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
         legend: { display: !!props.label, labels: { color: '#8290a6', font: { family: 'DM Mono' } } },
         tooltip: { mode: 'index', intersect: false, backgroundColor: '#151c28', borderColor: 'rgba(152,171,197,.15)', borderWidth: 1, titleFont: { family: 'DM Mono' }, bodyFont: { family: 'DM Mono' } },
      },
      scales: {
        x: {
           ticks: { color: '#8290a6', maxTicksLimit: 8 },
           grid: { color: 'rgba(152,171,197,.08)' },
        },
        y: {
           ticks: { color: '#8290a6' },
           grid: { color: 'rgba(152,171,197,.08)' },
        },
      },
    },
  })
}

watch(() => props.data, renderChart, { deep: true })

onMounted(renderChart)
onUnmounted(() => {
  if (chart) chart.destroy()
})
</script>

<style scoped>
.chart-container {
  position: relative;
  height: 300px;
  width: 100%;
}
</style>
