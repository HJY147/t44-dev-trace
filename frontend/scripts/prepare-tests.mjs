// Tests live outside the frontend package at the user's requested tmp/ location.
import { lstatSync, mkdirSync, realpathSync, symlinkSync } from 'node:fs'
import { fileURLToPath } from 'node:url'

const temporary = fileURLToPath(new URL('../../tmp/', import.meta.url))
const dependencies = fileURLToPath(new URL('../node_modules', import.meta.url))
const link = fileURLToPath(new URL('../../tmp/node_modules', import.meta.url))
mkdirSync(temporary, { recursive: true })
let exists = true
try { lstatSync(link) } catch (error) {
  if (error.code !== 'ENOENT') throw error
  exists = false
}
if (!exists) symlinkSync(dependencies, link, 'dir')
if (realpathSync(link) !== realpathSync(dependencies)) {
  throw new Error('tmp/node_modules must reference this frontend package dependencies')
}
