import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import path from 'path'

export default defineConfig({
  plugins: [react()],
  base: './',
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src'),
    },
  },
  build: {
    outDir: '../spa_sqladmin/statics/admin-ui',
    emptyOutDir: true,
    rollupOptions: {
      output: {
        manualChunks: {
          'vendor-tanstack': ['@tanstack/react-router', '@tanstack/react-table', '@tanstack/react-query'],
          'vendor-ui': ['lucide-react', 'react-day-picker', 'date-fns'],
        },
      },
    },
  },
})
