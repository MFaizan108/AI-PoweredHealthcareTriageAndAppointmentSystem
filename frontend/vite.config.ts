import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// All API calls in this app use relative paths (e.g. `/api/accounts/login/`) rather than an
// absolute base URL — that works unchanged in both places this app runs:
//   - dev: Vite's own server proxies /api, /health, /media to the Django dev server (below)
//   - prod: nginx proxies the same paths to the `web` container (see nginx/templates)
export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    proxy: {
      '/api': 'http://127.0.0.1:8000',
      '/health': 'http://127.0.0.1:8000',
      '/media': 'http://127.0.0.1:8000',
    },
  },
})
