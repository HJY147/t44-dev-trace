import vue from '@vitejs/plugin-vue'
import { defineConfig } from 'vitest/config'

export default defineConfig({
  plugins: [vue()],
  base: '/',
  build: { outDir: 'dist' },
  test: {
    environment: 'happy-dom',
    include: ['tests/**/*.test.ts'],
    server: { deps: { inline: ['element-plus'] } },
  },
})
