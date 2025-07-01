/*
import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// https://vite.dev/config/
export default defineConfig({
  plugins: [react()],
})
*/
import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// https://vite.dev/config/
export default defineConfig({
  plugins: [react()],
  server: {
    proxy: {
      // 프론트의 /stream/** 요청을 백엔드 localhost:8000/stream/** 으로 포워딩
      '/stream': {
        target: 'http://localhost:8000',
        changeOrigin: true,
        // path 그대로 전달하므로 rewrite는 없어도 되지만, 혹시 prefix를 바꾸고 싶다면 사용
        rewrite: (path) => path.replace(/^\/stream/, '/stream')
      }
    }
  }
})
