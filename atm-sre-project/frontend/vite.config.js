import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  server: {
    port: 3000,
    proxy: {
      '/auth': 'http://localhost:8000',
      '/account': 'http://localhost:8000',
      '/transaction': 'http://localhost:8000',
      '/history': 'http://localhost:8000',
      '/card': 'http://localhost:8000',
    },
  },
})
