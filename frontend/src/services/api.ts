import axios from 'axios'

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000/api'

const apiClient = axios.create({
  baseURL: API_URL,
})

export const authService = {
  register: (username: string, email: string, password: string) =>
    apiClient.post('/auth/register', { username, email, password }),
  
  login: (username: string, password: string) =>
    apiClient.post('/auth/login', { username, password }),
  
  getCurrentUser: () =>
    apiClient.get('/auth/me'),
}

export const marketService = {
  getPairs: (chainId?: string, watchedOnly?: boolean) =>
    apiClient.get('/market/pairs', { params: { chain_id: chainId, watched_only: watchedOnly } }),
  
  getPairSnapshots: (pairId: string, limit?: number) =>
    apiClient.get(`/market/pairs/${pairId}/snapshots`, { params: { limit } }),
  
  getPairSignals: (pairId: string, limit?: number) =>
    apiClient.get(`/market/pairs/${pairId}/signals`, { params: { limit } }),
  
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

export default apiClient
