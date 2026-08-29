<template>
  <div class="container">
    <div class="card">
      <div class="card-title">Dashboard</div>
      <div class="dashboard-grid">
        <div class="stat-card">
          <div class="stat-label">Bot Status</div>
          <div class="stat-value" :class="botStatus">{{ botStatus }}</div>
        </div>
        <div class="stat-card">
          <div class="stat-label">Trading Mode</div>
          <div class="stat-value">{{ tradingMode }}</div>
        </div>
        <div class="stat-card">
          <div class="stat-label">Active Positions</div>
          <div class="stat-value">0</div>
        </div>
        <div class="stat-card">
          <div class="stat-label">Total PnL</div>
          <div class="stat-value">$0.00</div>
        </div>
      </div>
    </div>

    <div class="card">
      <div class="card-title">Bot Controls</div>
      <div class="button-group">
        <button @click="startBot" class="btn btn-success">Start</button>
        <button @click="stopBot" class="btn btn-warning">Stop</button>
        <button @click="pauseBot" class="btn btn-info">Pause</button>
        <button @click="emergencyStop" class="btn btn-danger">Emergency Stop</button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { botService } from '../services/api'

const botStatus = ref('STOPPED')
const tradingMode = ref('PAPER')

const loadBotStatus = async () => {
  try {
    const response = await botService.getStatus()
    botStatus.value = response.data.state
    tradingMode.value = response.data.trading_mode
  } catch (err) {
    console.error('Error loading bot status:', err)
  }
}

const startBot = async () => {
  try {
    await botService.start()
    await loadBotStatus()
  } catch (err) {
    console.error('Error starting bot:', err)
  }
}

const stopBot = async () => {
  try {
    await botService.stop()
    await loadBotStatus()
  } catch (err) {
    console.error('Error stopping bot:', err)
  }
}

const pauseBot = async () => {
  try {
    await botService.pause()
    await loadBotStatus()
  } catch (err) {
    console.error('Error pausing bot:', err)
  }
}

const emergencyStop = async () => {
  if (confirm('Are you sure? This will stop all trading immediately.')) {
    try {
      await botService.emergencyStop()
      await loadBotStatus()
    } catch (err) {
      console.error('Error emergency stopping:', err)
    }
  }
}

onMounted(() => {
  loadBotStatus()
})
</script>

<style scoped>
.dashboard-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 1rem;
  margin-bottom: 2rem;
}

.stat-card {
  background-color: #2a2a2a;
  padding: 1.5rem;
  border-radius: 0.5rem;
  border: 1px solid #444;
}

.stat-label {
  color: #a0a0a0;
  font-size: 0.875rem;
  margin-bottom: 0.5rem;
}

.stat-value {
  font-size: 1.75rem;
  font-weight: bold;
}

.stat-value.STOPPED {
  color: #dc3545;
}

.stat-value.RUNNING {
  color: #28a745;
}

.stat-value.PAUSED {
  color: #ffc107;
}

.stat-value.EMERGENCY_STOP {
  color: #dc3545;
}

.button-group {
  display: flex;
  gap: 1rem;
  flex-wrap: wrap;
}

.btn-info {
  background-color: #17a2b8;
  color: white;
}

.btn-info:hover {
  background-color: #138496;
}
</style>
