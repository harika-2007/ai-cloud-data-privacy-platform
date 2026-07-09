import { defineConfig, loadEnv } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig(({ mode }) => {
  // Load env vars from .env files — VITE_API_URL takes precedence
  const env = loadEnv(mode, process.cwd(), '')

  const apiTarget = env.VITE_API_URL
    ? env.VITE_API_URL.replace('/api/v1', '')
    : 'http://localhost:8000'

  return {
    plugins: [react()],
    server: {
      port: 5173,
      // Proxy /api to the backend during local development
      proxy: {
        '/api': {
          target: apiTarget,
          changeOrigin: true,
          // Rewrite /api/v1 prefix if VITE_API_URL already includes it
        },
      },
    },
  }
})
