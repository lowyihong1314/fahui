// frontend/vite.config.js
import { defineConfig } from 'vite'
import path from 'path'

export default defineConfig({
  root: __dirname,

  server: {
    port: 5173,

    proxy: {
      '/static': {
        target: 'http://127.0.0.1:5015',
        changeOrigin: true
      },
      '/api': {
        target: 'http://127.0.0.1:5015',
        changeOrigin: true
      },
      '/auth': {
        target: 'http://127.0.0.1:5015',
        changeOrigin: true
      }
    }
  },

  build: {
    outDir: path.resolve(__dirname, '../static/vite'),
    emptyOutDir: true,
    rollupOptions: {
      input: path.resolve(__dirname, 'src/init.js'),
      output: {
        entryFileNames: 'init.js'
      }
    }
  }
})
