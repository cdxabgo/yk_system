import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'

export default defineConfig({
  plugins: [vue()],
  server: {
    port: 3000,
    proxy: {
      // Java 后端（包含 SSE 实时推送 /api/realtime/stream）
      '/api': {
        target: 'http://localhost:8081',
        changeOrigin: true
      },
      // Python REST API（用于启动/停止 MQTT 监测）
      '/python': {
        target: 'http://localhost:5000',
        changeOrigin: true,
        rewrite: (path) => path.replace(/^\/python/, '')
      }
    }
  }
})
