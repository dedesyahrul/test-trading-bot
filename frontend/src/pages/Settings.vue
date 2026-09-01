<template>
  <div class="container">
    <div class="card">
      <div class="card-title">Trading Settings</div>

      <div v-if="loading" class="loading">
        <div class="spinner"></div>
        Loading settings...
      </div>

      <div v-else-if="error" class="error-message">{{ error }}</div>

      <form v-else @submit.prevent="saveSettings" class="settings-form">
        <div class="form-section">
          <h3>Trading Mode</h3>
          <div class="form-group">
            <label>Mode</label>
            <select v-model="form.trading_mode" class="form-input">
              <option value="PAPER">Paper Trading</option>
              <option value="LIVE">Live Trading</option>
            </select>
            <p class="form-hint" v-if="form.trading_mode === 'LIVE'">
              Live mode uses real funds. Ensure wallet and risk limits are configured.
            </p>
            <p class="form-hint" v-else>
              Paper mode uses virtual funds only. Save this setting, then start the engine from the Dashboard.
            </p>
          </div>
        </div>

        <div class="form-section">
          <h3>Risk Management</h3>
          <div class="form-grid">
            <div class="form-group">
              <label>Max Position Size (USD)</label>
              <input v-model.number="form.risk_config.max_position_size_usd" type="number" class="form-input" min="0" />
            </div>
            <div class="form-group">
              <label>Max Daily Loss (USD)</label>
              <input v-model.number="form.risk_config.max_daily_loss_usd" type="number" class="form-input" min="0" />
            </div>
            <div class="form-group">
              <label>Max Open Positions</label>
              <input v-model.number="form.risk_config.max_positions" type="number" class="form-input" min="1" />
            </div>
            <div class="form-group">
              <label>Min Liquidity (USD)</label>
              <input v-model.number="form.risk_config.min_liquidity_usd" type="number" class="form-input" min="0" />
            </div>
            <div class="form-group">
              <label>Max Risk Score</label>
              <input v-model.number="form.risk_config.max_risk_score" type="number" class="form-input" min="0" max="100" />
            </div>
            <div class="form-group">
              <label>Paper Initial Balance (USD)</label>
              <input v-model.number="form.risk_config.paper_initial_balance" type="number" class="form-input" min="1" step="1" />
              <p class="form-hint">Virtual balance only. This never funds live trades.</p>
            </div>
          </div>
        </div>

        <div class="form-section" v-for="strategy in form.strategies" :key="strategy.id">
          <h3>{{ strategy.name }}</h3>
          <p class="form-hint">{{ strategy.description }}</p>
          <div class="form-group">
            <label class="checkbox-label">
              <input type="checkbox" v-model="strategy.enabled" />
              Enabled
            </label>
          </div>
          <div class="form-grid">
            <div class="form-group" v-for="(value, key) in strategy.parameters" :key="key">
              <label>{{ formatParamLabel(key) }}</label>
              <input
                v-model.number="strategy.parameters[key]"
                type="number"
                step="0.01"
                class="form-input"
              />
            </div>
          </div>
        </div>

        <div class="button-group">
          <button type="submit" class="btn btn-primary" :disabled="saving">
            {{ saving ? 'Saving...' : 'Save Settings' }}
          </button>
          <button type="button" @click="loadSettings" class="btn btn-warning">Reset</button>
        </div>

        <div v-if="successMessage" class="success-message">{{ successMessage }}</div>
      </form>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { settingsService } from '../services/api'

interface StrategyForm {
  id: string
  name: string
  description: string
  enabled: boolean
  parameters: Record<string, number>
}

interface RiskConfig {
  max_position_size_usd: number
  max_daily_loss_usd: number
  max_positions: number
  min_liquidity_usd: number
  max_risk_score: number
}

const loading = ref(true)
const saving = ref(false)
const error = ref('')
const successMessage = ref('')

const form = ref({
  trading_mode: 'PAPER',
  risk_config: {
    max_position_size_usd: 1000,
    max_daily_loss_usd: 500,
    max_positions: 5,
    min_liquidity_usd: 5000,
    max_risk_score: 50,
  } as RiskConfig,
  strategies: [] as StrategyForm[],
})

const formatParamLabel = (key: string) => {
  return key.replace(/_/g, ' ').replace(/\b\w/g, (c) => c.toUpperCase())
}

const loadSettings = async () => {
  loading.value = true
  error.value = ''
  try {
    const response = await settingsService.getTrading()
    const data = response.data
    form.value.trading_mode = data.trading_mode
    form.value.risk_config = data.risk_config
    form.value.strategies = data.strategies.map((s: StrategyForm) => ({
      ...s,
      parameters: { ...s.parameters },
    }))
  } catch (err: any) {
    error.value = err.response?.data?.detail || 'Failed to load settings'
  } finally {
    loading.value = false
  }
}

const saveSettings = async () => {
  saving.value = true
  error.value = ''
  successMessage.value = ''
  try {
    await settingsService.updateTrading({
      trading_mode: form.value.trading_mode,
      risk_config: form.value.risk_config,
      strategies: form.value.strategies.map((s) => ({
        strategy_id: s.id,
        enabled: s.enabled,
        parameters: s.parameters,
      })),
    })
    successMessage.value = 'Settings saved successfully'
  } catch (err: any) {
    error.value = err.response?.data?.detail || 'Failed to save settings'
  } finally {
    saving.value = false
  }
}

onMounted(loadSettings)
</script>

<style scoped>
.settings-form {
  display: flex;
  flex-direction: column;
  gap: 2rem;
}

.form-section h3 {
  margin-bottom: 1rem;
  color: #fff;
  border-bottom: 1px solid #333;
  padding-bottom: 0.5rem;
}

.form-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
  gap: 1rem;
}

.form-group {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.form-group label {
  font-size: 0.875rem;
  color: #aaa;
}

.form-hint {
  font-size: 0.8rem;
  color: #888;
  margin-bottom: 0.5rem;
}

.checkbox-label {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  cursor: pointer;
}

.success-message {
  color: #28a745;
  padding: 0.75rem;
  background: rgba(40, 167, 69, 0.1);
  border-radius: 0.25rem;
}

.error-message {
  color: #dc3545;
  padding: 0.75rem;
}
</style>
