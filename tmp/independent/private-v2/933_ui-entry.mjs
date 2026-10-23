#!/usr/bin/env node
// Preserve frozen935bytes; decode the local Unicode file URL only for evidence-directory placement.
import fs from 'node:fs';
import {fileURLToPath} from 'node:url';
const filename=fileURLToPath(new URL('./935_ui-driver.mjs',import.meta.url));
process.argv[1]=filename;
const original=fs.readFileSync(filename,'utf8');
const adapted=original.replace('new URL(import.meta.url).pathname','process.argv[1]');
if(adapted===original)throw new Error('Expected frozen evidence-path expression absent');
await import('data:text/javascript;base64,'+Buffer.from(adapted).toString('base64'));
