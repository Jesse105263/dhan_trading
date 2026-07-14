import react from '@vitejs/plugin-react'
import { defineConfig, loadEnv } from 'vite'

export default defineConfig(({ mode }) => {
  const environment = loadEnv(mode, process.cwd(), '')
  const apiTarget = environment.VITE_API_PROXY_TARGET?.trim()

  return {
    plugins: [react()],
    server: {
      host: '127.0.0.1',
      proxy: apiTarget
        ? {
            '/api': { target: apiTarget, changeOrigin: false },
            '/health': { target: apiTarget, changeOrigin: false },
          }
        : undefined,
    },
    test: {
      environment: 'jsdom',
      setupFiles: './src/test/setup.ts',
      css: true,
    },
  }
})
