#!/usr/bin/env node
// Syntax/output-path adapter only; preserves935/933 bytes and original946 UI assertions.
import fs from 'node:fs';
import {fileURLToPath} from 'node:url';
const filename=fileURLToPath(new URL('./935_ui-driver.mjs',import.meta.url));
process.argv[1]=filename;
const original=fs.readFileSync(filename,'utf8');
const adapted=original.replace('new URL(import.meta.url).pathname','process.argv[1]').replace("from '/Users/yang/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/playwright/index.mjs'","from 'file:///Users/yang/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/playwright/index.mjs'");
if(adapted===original)throw new Error('Expected frozen runtimeexpressions absent');
await import('data:text/javascript;base64,'+Buffer.from(adapted).toString('base64'));
