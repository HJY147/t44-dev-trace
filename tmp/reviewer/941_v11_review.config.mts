// ROLE-reviewer-V11-IMPLEMENTATION-v1; only rerun unchanged original 959 assertions.
import vue from '@vitejs/plugin-vue'
import { defineConfig } from 'vitest/config'
import { fileURLToPath } from 'node:url'
export default defineConfig({ plugins: [vue()], test: { root: fileURLToPath(new URL('../../', import.meta.url)), environment: 'happy-dom', include: ['tmp/reviewer/959_ui_contract_probe.mjs'], server: { deps: { inline: ['element-plus'] } } } })
