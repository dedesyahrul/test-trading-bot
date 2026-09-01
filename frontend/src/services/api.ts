import axios from 'axios'

// Production Nginx proxies /api to the backend. Same-origin URLs work from
// localhost, a VPS IP, and a domain without rebuilding per host.
const configuredApiUrl = import.meta.env.VITE_API_URL || ''
const isRemoteHost = typeof window !== 'undefined' && !['localhost', '127.0.0.1'].includes(window.location.hostname)
const API_URL = isRemoteHost && configuredApiUrl.includes('localhost') ? '/api' : (configuredApiUrl || '/api')

const apiClient = axios.create({
  baseURL: API_URL,
})

apiClient.interceptors.request.use((config) => {
  const token = localStorage.getItem('access_token')
  if (token) {
    config.headers = config.headers || {}
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

apiClient.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401 && !error.config?.url?.includes('/auth/login')) {
      // A token can become invalid after a backend restart or secret rotation.
      // Remove it so the router cannot keep rendering a broken authenticated session.
      localStorage.removeItem('access_token')
      if (window.location.pathname !== '/login') window.location.assign('/login')
    }
    return Promise.reject(error)
  },
)

export const authService = {
  register: (username: string, email: string, password: string) =>
    apiClient.post('/auth/register', { username, email, password }),

  login: (username: string, password: string) =>
    apiClient.post('/auth/login', null, { params: { username, password } }),

  getCurrentUser: () =>
    apiClient.get('/auth/me'),
}

export const marketService = {
  discover: () => apiClient.post('/market/discover'),

  getPairs: (chainId?: string, watchedOnly?: boolean) =>
    apiClient.get('/market/pairs', { params: { chain_id: chainId, watched_only: watchedOnly } }),

  getPairsPage: (params: { page?: number; page_size?: number; search?: string; risk_level?: string; sort_by?: string; sort_dir?: string }) =>
    apiClient.get('/market/pairs/page', { params }),

  getPairSnapshots: (pairId: string, limit?: number) =>
    apiClient.get(`/market/pairs/${pairId}/snapshots`, { params: { limit } }),

  getPairSignals: (pairId: string, limit?: number) =>
    apiClient.get(`/market/pairs/${pairId}/signals`, { params: { limit } }),

  getChartIntelligence: (pairId: string, timeframe = 'minute') =>
    apiClient.get(`/market/pairs/${pairId}/chart-intelligence`, { params: { timeframe } }),

  getCandles: (pairId: string, timeframe = 'minute', limit = 100) =>
    apiClient.get(`/market/pairs/${pairId}/candles`, { params: { timeframe, limit } }),

  watchPair: (pairId: string) =>
    apiClient.post(`/market/pairs/${pairId}/watch`),

  unwatchPair: (pairId: string) =>
    apiClient.post(`/market/pairs/${pairId}/unwatch`),
}

export const botService = {
  getStatus: () =>
    apiClient.get('/bot/status'),

  start: () =>
    apiClient.post('/bot/start'),

  stop: () =>
    apiClient.post('/bot/stop'),

  pause: () =>
    apiClient.post('/bot/pause'),

  emergencyStop: () =>
    apiClient.post('/bot/emergency-stop'),

  reset: () =>
    apiClient.post('/bot/reset'),
}

export const settingsService = {
  getTrading: () => apiClient.get('/settings/trading'),
  updateTrading: (config: object) => apiClient.put('/settings/trading', config),
  getStrategies: () => apiClient.get('/settings/strategies'),
  updateStrategy: (strategyId: string, config: object) =>
    apiClient.put(`/settings/strategies/${strategyId}`, config),
  getRisk: () => apiClient.get('/settings/risk'),
  updateRisk: (config: object) => apiClient.put('/settings/risk', config),
}

export const statisticsService = {
  getSummary: () => apiClient.get('/statistics/summary'),
  getDaily: (days?: number) => apiClient.get('/statistics/daily', { params: { days } }),
  getPaperValidation: () => apiClient.get('/statistics/paper-validation'),
}

export const systemService = {
  getStatus: () => apiClient.get('/system/status'),
}

export const auditService = {
  list: (action?: string, resource?: string, limit = 100) =>
    apiClient.get('/audit/logs', { params: { action, resource, limit } }),
}

export const riskService = {
  getPortfolio: () => apiClient.get('/risk/portfolio'),
}

export const watchlistService = {
  history: (params?: { page?: number; page_size?: number; search?: string; action?: string }) =>
    apiClient.get('/watchlist/history', { params }),
}

export const portfolioService = {
  getDefaultWallet: () => apiClient.get('/portfolio/wallets/default'),
  listPositions: (status?: string, walletId?: string) =>
    apiClient.get('/portfolio/positions', { params: { status, wallet_id: walletId } }),
  getSummary: (walletId: string) => apiClient.get(`/portfolio/summary/${walletId}`),
  getPosition: (positionId: string) => apiClient.get(`/portfolio/positions/${positionId}`),
  closePosition: (positionId: string) => apiClient.post(`/portfolio/positions/${positionId}/close`),
}

export default apiClient
