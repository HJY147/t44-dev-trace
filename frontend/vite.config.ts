import vue from '@vitejs/plugin-vue'
import { defineConfig } from 'vitest/config'

export default defineConfig({
  plugins: [vue()],
  base: '/',
  server: { proxy: { '/api/v1': { target: 'http://127.0.0.1:18080', changeOrigin: false } } },
  build: { outDir: 'dist' },
  test: {
    environment: 'happy-dom',
    include: ['tests/**/*.test.ts'],
    server: { deps: { inline: ['element-plus'] } },
    coverage: { provider: 'v8', include: ['src/**/*.{ts,vue}'], reporter: ['text', 'json-summary', 'json', 'html'], thresholds: { lines: 80 } },
  },
})
