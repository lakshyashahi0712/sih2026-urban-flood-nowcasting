import react from '@vitejs/plugin-react'
import { defineConfig, loadEnv } from 'vite'

// https://vite.dev/config/
export default defineConfig(({ mode }) => {
  const env = loadEnv(mode, process.cwd(), '')
  const API_TARGET =
    process.env.VITE_API_TARGET ||
    env.VITE_API_TARGET ||
    'http://localhost:8000'

  const PROXY_CONFIG = {
    '/api': { target: API_TARGET, changeOrigin: true },
    '/flood': { target: API_TARGET, changeOrigin: true },
    '/rainfall': { target: API_TARGET, changeOrigin: true },
    '/routing': { target: API_TARGET, changeOrigin: true },
    '/health': { target: API_TARGET, changeOrigin: true },
    '/ready': { target: API_TARGET, changeOrigin: true },
  }

  return {
    plugins: [react()],
    server: {
      proxy: PROXY_CONFIG,
    },
    preview: {
      proxy: PROXY_CONFIG,
    },
  }
})
