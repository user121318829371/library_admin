import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'

export default defineConfig({
  plugins: [vue()],
  server: {
    port: 5173,
    // 固定监听 IPv4 回环，ngrok 直接转发到 127.0.0.1:5173
    host: '127.0.0.1',
    // 端口被占用时直接报错，避免 ngrok 指向错误的端口
    strictPort: true,
    // 允许通过 ngrok 公网域名访问（Vite 5.4+ 默认会拦截未知 Host）
    allowedHosts: ['.ngrok-free.app', '.ngrok.app', '.ngrok.io', '.ngrok-free.dev'],
    proxy: {
      '/api': {
        target: 'http://127.0.0.1:8000',
        changeOrigin: true,
      },
    },
  },
})
