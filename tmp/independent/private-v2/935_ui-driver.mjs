#!/usr/bin/env node
// Independent blackbox browser driver for the pre-SUT frozen946 UI protocol.
// Uses rendered DOM and actual HTTP observations, never product source/module imports.
import fs from 'node:fs';
import path from 'node:path';
import crypto from 'node:crypto';
import readline from 'node:readline';
import {chromium} from '/Users/yang/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/playwright/index.mjs';
const base='http://127.0.0.1:5175';
const credentials=JSON.parse(fs.readFileSync('/Users/yang/Desktop/nothing/软件开发大作业/.agent-worktrees/.runtime/local-acceptance-v2/ui-credentials.json','utf8'));
const secretValues=Object.values(credentials).map(x=>x.password).filter(Boolean);
const out=path.resolve(path.dirname(new URL(import.meta.url).pathname),'ui-4c20-private');
fs.mkdirSync(out,{recursive:true,mode:0o700});fs.chmodSync(out,0o700);
const events=path.join(out,'ui-events.jsonl');let currentCase='CAPABILITY';const steps=[],network=[],errors=[];
function clean(v){if(Array.isArray(v))return v.map(clean);if(v&&typeof v==='object')return Object.fromEntries(Object.entries(v).map(([k,x])=>[k,/password|authorization|token|secret|cookie/i.test(k)?'<redacted>':clean(x)]));if(typeof v==='string'){for(const x of secretValues)v=v.split(x).join('<redacted>');return v;}return v;}
function log(kind,data){fs.appendFileSync(events,JSON.stringify(clean({at:new Date().toISOString(),case:currentCase,kind,...data}))+'\n',{mode:0o600});}
function reply(v){process.stdout.write(JSON.stringify(clean(v))+'\n');}
const browser=await chromium.launch({headless:true,executablePath:'/Applications/Google Chrome.app/Contents/MacOS/Google Chrome'});
let context=await browser.newContext({viewport:{width:1360,height:980},locale:'zh-CN',timezoneId:'Asia/Shanghai'});
let page=await context.newPage();
function bind(p){p.on('console',m=>{const x={type:m.type(),text:m.text()};if(m.type()==='error')errors.push(x);log('console',x);});p.on('pageerror',e=>{errors.push({type:'pageerror',text:e.message});log('pageerror',{message:e.message});});p.on('response',async r=>{const u=new URL(r.url());if(!u.pathname.startsWith('/api/v1'))return;const x={path:u.pathname,query:u.search,method:r.request().method(),status:r.status()};try{const v=await r.json();x.request_id=v.meta?.request_id||v.request_id;x.code=v.code;if(u.pathname==='/api/v1/auth/login'&&v.data?.access_token)secretValues.push(v.data.access_token);}catch{}network.push(x);log('network',x);});}
bind(page);await page.goto(base,{waitUntil:'networkidle'});
async function snapshot(){const body=await page.locator('body').innerText();const controls=await page.locator('input,textarea,select,button,a,[role="button"],[role="combobox"]').evaluateAll(xs=>xs.filter(x=>x.getClientRects().length).map(x=>({tag:x.tagName.toLowerCase(),type:x.getAttribute('type'),id:x.id,name:x.getAttribute('name'),role:x.getAttribute('role'),placeholder:x.getAttribute('placeholder'),label:x.getAttribute('aria-label'),text:(x.innerText||'').trim().slice(0,100),value:x.getAttribute('type')==='password'?'<masked>':(x.value??''),href:x.getAttribute('href')})));return {url:page.url(),body:body.slice(0,18000),controls};}
function locator(c){if(c.role)return page.getByRole(c.role,{name:c.name,exact:c.exact??true});if(c.text)return page.getByText(c.text,{exact:c.exact??true});if(c.label)return page.getByLabel(c.label,{exact:c.exact??true});return page.locator(c.selector);}
reply({ready:true,browser:browser.version(),headless:true,viewport:{width:1360,height:980},timezone:'Asia/Shanghai',snapshot:await snapshot()});
const rl=readline.createInterface({input:process.stdin,crlfDelay:Infinity});
for await(const line of rl){if(!line.trim())continue;let c;try{c=JSON.parse(line);if(c.case)currentCase=c.case;log('command',{...c,value:c.credential?'<credential reference>':c.value});let result;
 if(c.cmd==='snapshot')result=await snapshot();
 else if(c.cmd==='click'){await locator(c).click();await page.waitForLoadState('networkidle');result=await snapshot();}
 else if(c.cmd==='fill'){const value=c.credential?credentials[c.credential.role][c.credential.field]:c.value;await locator(c).fill(String(value));result=await snapshot();}
 else if(c.cmd==='select'){await locator(c).selectOption(c.value);result=await snapshot();}
 else if(c.cmd==='check'){await locator(c).check();result=await snapshot();}
 else if(c.cmd==='key'){await page.keyboard.press(c.key);result=await snapshot();}
 else if(c.cmd==='goto'){const u=new URL(c.url,base);if(u.origin!==base)throw Error('Navigation outside bound local origin refused');await page.goto(u.href,{waitUntil:'networkidle'});result=await snapshot();}
 else if(c.cmd==='reload'){await page.reload({waitUntil:'networkidle'});result=await snapshot();}
 else if(c.cmd==='back'){await page.goBack({waitUntil:'networkidle'});result=await snapshot();}
 else if(c.cmd==='resize'){await page.setViewportSize({width:c.width,height:c.height});result=await snapshot();}
 else if(c.cmd==='screenshot'){const name=String(c.name||currentCase).replace(/[^A-Za-z0-9_.-]/g,'_')+'.png';await page.screenshot({path:path.join(out,name),fullPage:true});result={file:name,sha256:crypto.createHash('sha256').update(fs.readFileSync(path.join(out,name))).digest('hex')};}
 else if(c.cmd==='expect'){await locator(c).waitFor({state:c.state||'visible'});result={passed:true,expectation:c.expectation||c.text||c.name};steps.push({case:currentCase,...result});}
 else if(c.cmd==='network')result=network.slice(-(c.last||20));
 else if(c.cmd==='errors')result=errors;
 else if(c.cmd==='role'){await context.close();context=await browser.newContext({viewport:{width:1360,height:980},locale:'zh-CN',timezoneId:'Asia/Shanghai'});page=await context.newPage();bind(page);await page.goto(base,{waitUntil:'networkidle'});result=await snapshot();}
 else if(c.cmd==='finish'){fs.writeFileSync(path.join(out,'ui-results.json'),JSON.stringify(clean({product_source_sha:'4c20f32b71635016815420472b9d4bb4fa850df0',operator:'independent AI',browser:browser.version(),headless:true,steps,errors,network,overall:'UNREVIEWED_PARTIAL_UI_OBSERVATIONS'}),null,2)+'\n',{mode:0o600});await browser.close();reply({closed:true});break;}
 else throw Error('Unsupported UI command');
 log('observation',{command:c.cmd,result});reply({ok:true,result});
 }catch(e){const failure={case:currentCase,command:c?.cmd,error:e.message};steps.push({...failure,passed:false});log('driver_error',failure);reply({ok:false,...failure});}}
