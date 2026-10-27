import path from 'node:path'
import tailwindcss from '@tailwindcss/vite'
import react from '@vitejs/plugin-react'
// defineConfig de vitest/config es el de Vite mas la seccion "test".
import { defineConfig } from 'vitest/config'

// https://vite.dev/config/
export default defineConfig({
  plugins: [react(), tailwindcss()],
  resolve: {
    alias: {
      '@': path.resolve(import.meta.dirname, './src'),
    },
  },
  test: {
    environment: 'jsdom',
    // Hora de Chile fija: las fechas relativas y la proxima revision dependen de la zona.
    env: { TZ: 'America/Santiago' },
  },
})
