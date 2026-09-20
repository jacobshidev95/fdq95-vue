import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import { fileURLToPath, URL } from 'node:url'

// ★ 每次构建生成唯一 ID，产物文件名必变
const buildId = `${Date.now().toString(36)}-${Math.random().toString(36).slice(2, 7)}`

export default defineConfig({
  plugins: [vue()],
  resolve: {
    alias: {
      '@': fileURLToPath(new URL('./src', import.meta.url)),
    },
  },
  build: {
    rollupOptions: {
      output: {
        entryFileNames: `assets/[name]-${buildId}.js`,
        chunkFileNames: `assets/[name]-${buildId}.js`,
        assetFileNames: `assets/[name]-${buildId}.[ext]`,
      },
    },
  },
  server: {
    host: '0.0.0.0',
    port: 5173,
    proxy: {
      '/api': { target: 'http://localhost:8080', changeOrigin: true },
      '/auth': { target: 'http://localhost:8080', changeOrigin: true },
      '/users': { target: 'http://localhost:8080', changeOrigin: true },
      '/health': { target: 'http://localhost:8080', changeOrigin: true },
    },
  },
})