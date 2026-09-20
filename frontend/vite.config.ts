import react from '@vitejs/plugin-react'
import { defineConfig } from 'vite'

// Backend origin for the dev proxy (override with VITE_API_TARGET if needed).
const API_TARGET = process.env.VITE_API_TARGET || 'http://localhost:8000'

// https://vite.dev/config/
export default defineConfig({
  plugins: [react()],
  server: {
    proxy: {
      '/api': { target: API_TARGET, changeOrigin: true },
      '/flood': { target: API_TARGET, changeOrigin: true },
      '/rainfall': { target: API_TARGET, changeOrigin: true },
      '/routing': { target: API_TARGET, changeOrigin: true },
      '/health': { target: API_TARGET, changeOrigin: true },
      '/ready': { target: API_TARGET, changeOrigin: true },
    },
  },
})
