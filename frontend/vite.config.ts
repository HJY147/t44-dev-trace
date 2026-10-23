import vue from '@vitejs/plugin-vue'
import { fileURLToPath } from 'node:url'
import { defineConfig } from 'vitest/config'

export default defineConfig({
  plugins: [vue()],
  publicDir: fileURLToPath(new URL('./public', import.meta.url)),
  base: '/',
  server: { proxy: { '/api/v1': { target: 'http://127.0.0.1:18080', changeOrigin: false } } },
  build: { outDir: 'dist' },
  test: {
    root: '..',
    environment: 'happy-dom',
    include: ['tmp/frontend/[0-9][0-9][0-9]_*.test.ts'],
    server: { deps: { inline: ['element-plus'] } },
    coverage: { provider: 'v8', include: ['frontend/src/**/*.{ts,vue}'], reportsDirectory: 'frontend/coverage', reporter: ['text', 'json-summary', 'json', 'html'], thresholds: { lines: 80 } },
  },
})
