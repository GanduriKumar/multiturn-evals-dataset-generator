import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// https://vite.dev/config/
export default defineConfig({
  plugins: [react()],
  server: {
    proxy: {
      '/config': 'http://localhost:8000',
      '/generate-dataset': 'http://localhost:8000',
      '/score-run': 'http://localhost:8000',
    },
  },
})
