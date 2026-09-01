import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'

export default defineConfig({
  plugins: [vue()],
  server: {
    port: parseInt(process.env.FRONTEND_PORT || '3000'),
    host: '0.0.0.0',
    proxy: {
      '/api': {
        target: process.env.VITE_API_URL?.replace('/api', '') || 'http://localhost:17845',
        changeOrigin: true,
      }
    }
  }
})
