import { chromium } from '/Users/yang/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/playwright/index.mjs'
import { readFile, writeFile } from 'node:fs/promises'
import { resolve } from 'node:path'
const root = resolve('agents/reviewer/evidence/product-v1/diagrams')
const manifest = JSON.parse(await readFile(root + '/manifest.json', 'utf8'))
const browser = await chromium.launch({ channel: 'chrome', headless: true })
const page = await browser.newPage({ viewport: { width: 1800, height: 1200 }, deviceScaleFactor: 1 })
const result = { target_sha: 'e01f5dcf9d8ef5a88161fcbc87ab142fba74cdef', engine: await browser.version(), renderer: 'mermaid 11.12.0; local downloaded bundle SHA256 in renderer-source.json', diagrams: [] }
try {
  await page.setContent('<html><head><meta charset="utf-8"></head><body style="margin:24px;background:white"><div id="diagram"></div></body></html>')
  await page.addScriptTag({ path: '/tmp/t44-reviewer-mermaid-11.12.0.min.js' })
  await page.evaluate(() => mermaid.initialize({ startOnLoad: false, securityLevel: 'strict', theme: 'default', fontFamily: 'Arial, PingFang SC, sans-serif' }))
  for (const [index, item] of manifest.entries()) {
    try {
      const source = await readFile(root + '/' + item.name + '.mmd', 'utf8')
      const svg = await page.evaluate(async ({ source, index }) => (await mermaid.render('review' + index, source)).svg, { source, index })
      await writeFile(root + '/' + item.name + '.svg', svg)
      await page.locator('#diagram').evaluate((element, svg) => element.innerHTML = svg, svg)
      const dimensions = await page.locator('#diagram svg').evaluate(el => ({ width: el.getBoundingClientRect().width, height: el.getBoundingClientRect().height }))
      await page.locator('#diagram svg').screenshot({ path: root + '/' + item.name + '.png' })
      result.diagrams.push({ ...item, rendered: true, ...dimensions })
    } catch (error) { result.diagrams.push({ ...item, rendered: false, error: String(error) }) }
  }
} finally { await browser.close(); await writeFile(root + '/render-results.json', JSON.stringify(result, null, 2) + '\n') }
console.log(JSON.stringify(result))
if (result.diagrams.some(d => !d.rendered)) process.exitCode = 1
