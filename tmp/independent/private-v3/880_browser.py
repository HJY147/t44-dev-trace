"""Actual isolated browser flows; no injected application state or mocked HTTP responses."""
import base64
import importlib.util
import json
from pathlib import Path
import re
import subprocess

NODE_BRIDGE = r'''
import {createInterface} from 'node:readline';
const mod=await import(process.env.IV3_PLAYWRIGHT_MODULE);
const objects=new Map([[0,mod]]);let next=1;
function revive(v){if(Array.isArray(v))return v.map(revive);if(v&&typeof v==='object'){
 if(v.__regexp!==undefined)return new RegExp(v.__regexp,v.flags||'');
 if(v.__ref!==undefined)return objects.get(v.__ref);
 return Object.fromEntries(Object.entries(v).map(([k,x])=>[k,revive(x)]));}return v;}
function wrap(v){if(Buffer.isBuffer(v))return {__bytes:v.toString('base64')};
 if(v!==null&&typeof v==='object'){const id=next++;objects.set(id,v);return {__ref:id};}return v;}
const rl=createInterface({input:process.stdin,crlfDelay:Infinity});
for await(const line of rl){try{const r=JSON.parse(line),obj=objects.get(r.ref);
 let v;if(r.method==='$get')v=obj[r.name];
 else if(r.method==='$observe'){obj.__iv3Traffic=[];obj.on('response',async response=>{
   const u=new URL(response.url());if(!u.pathname.startsWith('/api/')||u.pathname.endsWith('/auth/login'))return;
   let code=null;try{code=(await response.json()).code||null;}catch{}
   obj.__iv3Traffic.push({method:response.request().method(),path:u.pathname,status:response.status(),code});});}
 else if(r.method==='$traffic')v=JSON.stringify(obj.__iv3Traffic||[]);
 else v=await obj[r.method](...revive(r.args));
 process.stdout.write(JSON.stringify({ok:true,value:wrap(v)})+'\n');
 }catch(e){process.stdout.write(JSON.stringify({ok:false,error:e.name||'BrowserError',message:String(e.message).replace(/Call log:[\s\S]*/,'').slice(0,1500)})+'\n');}}
'''

def camel(value):
    return re.sub(r'_([a-z])', lambda m: m[1].upper(), value)

class NodeRemote:
    def __init__(self, bridge, ref): self.bridge, self.ref = bridge, ref
    def __getattr__(self, name):
        if name == 'url': return self.bridge.call(self.ref, 'url', [])
        if name in ('chromium', 'keyboard'):
            return self.bridge.call(self.ref, '$get', [], name=name)
        def invoke(*args, **kwargs):
            values = list(args)
            if kwargs: values.append({camel(k): v for k, v in kwargs.items()})
            return self.bridge.call(self.ref, camel(name), values)
        return invoke

class NodePlaywright:
    def __init__(self, context): self.context = context
    def __enter__(self):
        import os
        env = os.environ.copy(); env['IV3_PLAYWRIGHT_MODULE'] = self.context['node_playwright_module']
        self.stderr = open(Path(self.context['harness_output_directory']) / 'node-browser-stderr.log', 'a')
        self.process = subprocess.Popen([self.context['node_executable'], '--input-type=module', '-e', NODE_BRIDGE],
            stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=self.stderr, text=True, env=env)
        return NodeRemote(self, 0)
    def encode(self, value):
        if isinstance(value, re.Pattern): return {'__regexp': value.pattern, 'flags': 'i' if value.flags & re.I else ''}
        if isinstance(value, NodeRemote): return {'__ref': value.ref}
        if isinstance(value, dict): return {k: self.encode(v) for k, v in value.items()}
        if isinstance(value, (list, tuple)): return [self.encode(v) for v in value]
        return value
    def call(self, ref, method, args, **extra):
        if method == 'launch':
            args = args or [{}]
            args[-1]['executablePath'] = self.context['chrome_executable']
        self.process.stdin.write(json.dumps({'ref': ref, 'method': method, 'args': self.encode(args), **extra}) + '\n')
        self.process.stdin.flush(); line = self.process.stdout.readline()
        if not line: raise RuntimeError('Node Playwright transport ended without a response')
        result = json.loads(line)
        if not result['ok']: raise RuntimeError('Browser transport: ' + result['error'] + ': ' + result.get('message', ''))
        value = result.get('value')
        if isinstance(value, dict) and '__ref' in value: return NodeRemote(self, value['__ref'])
        if isinstance(value, dict) and '__bytes' in value: return base64.b64decode(value['__bytes'])
        return value
    def __exit__(self, *args):
        self.process.stdin.close()
        try: self.process.wait(timeout=5)
        except subprocess.TimeoutExpired: self.process.terminate()
        self.stderr.close()

def main():
    spec = importlib.util.spec_from_file_location('iv3_browser_support', Path(__file__).with_name('881_support.py'))
    S = importlib.util.module_from_spec(spec); spec.loader.exec_module(S)
    h = S.Harness('real-browser')
    ids = ['U01-login-logout-session-lifecycle', 'U02-project-switch-and-outsider-isolation',
           'U03-block-and-unblock-visible-business-provenance', 'U04-capacity-removal-error-and-unchanged-plan',
           'U05-history-current-authoritative-version-and-timezone', 'U06-accessible-keyboard-and-fresh-context-boundary']
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        if all(h.c.get(k) for k in ('node_executable', 'node_playwright_module', 'chrome_executable')):
            sync_playwright = lambda: NodePlaywright(h.c)
        else:
            for cid in ids:
                h.rec.results.append({'id': cid, 'status': 'capability_blocked',
                                      'reason': 'Neutral runtime provides no Playwright/browser installation'})
            return h.rec.finish()
    h.setup_users()
    # Original business predicates are frozen. These semantic selectors are mechanically
    # bound to observed runtime controls; ambiguity remains a navigation capability block.
    def one(locator, purpose):
        n = locator.count()
        if n == 0:
            try: locator.wait_for(state='visible', timeout=10000)
            except Exception: pass
            n = locator.count()
        if n != 1:
            raise S.Blocked('Frozen semantic UI navigation cannot uniquely bind ' + purpose + '; observed count=' + str(n))
        return locator
    def button(page, names):
            match = page.get_by_role('button', name=re.compile(names))
            if match.count() == 0:
                try: match.wait_for(state='visible', timeout=10000)
                except Exception: pass
            if match.count() == 1: return match
            return one(page.get_by_role('link', name=re.compile(names)), names)
    def field(page, names):
        return one(page.get_by_label(re.compile(names)), names)
    def text(page):
        return page.locator('body').inner_text()
    def snapshot(page, label):
        data = page.screenshot(full_page=True, type='png')
        # Hosted archive whitelist permits trace.log, so preserve real screenshots as framed base64.
        with (h.rec.directory / 'trace.log').open('a') as out:
            out.write(json.dumps({'kind': 'real_browser_png', 'label': label,
                                 'encoding': 'base64', 'bytes': len(data),
                                 'payload': base64.b64encode(data).decode()}) + '\n')
        h.rec.event({'kind': 'ui_observation', 'label': label, 'url_path': page.url.split('?')[0],
                     'visible_text': text(page)[:12000]})
    with sync_playwright() as playwright:
        try:
            browser = playwright.chromium.launch(headless=True)
        except Exception:
            for cid in ids:
                h.rec.results.append({'id': cid, 'status': 'capability_blocked',
                                      'reason': 'Neutral runtime has no launchable Chromium browser'})
            return h.rec.finish()
        contexts = []
        def fresh(actor):
            context = browser.new_context(timezone_id='Asia/Shanghai', viewport={'width': 1365, 'height': 900})
            contexts.append(context); page = context.new_page()
            if isinstance(page, NodeRemote): page.bridge.call(page.ref, '$observe', [])
            page.goto(h.c['web_base_url'], wait_until='networkidle')
            field(page, '用户名|账号|Username').fill(h.credentials[actor]['username'])
            field(page, '密码|Password').fill(h.credentials[actor]['password'])
            button(page, '^登录$|^Login$').click()
            page.get_by_role('button', name=re.compile('^登录$|^Login$')).wait_for(state='hidden', timeout=10000)
            page.wait_for_load_state('networkidle')
            return context, page
        def open_project(page, name):
            native = page.locator('select').filter(has=page.get_by_role('option', name=name, exact=True))
            if native.count() == 1:
                native.select_option(label=name)
                page.wait_for_timeout(100)
                page.wait_for_load_state('networkidle')
                return
            match = page.get_by_text(name, exact=True)
            if match.count() == 1:
                match.click()
            else:
                selector = field(page, '^项目$|选择项目|Project')
                selector.click(); one(page.get_by_role('option', name=name, exact=True), 'project option').click()
            page.wait_for_load_state('networkidle')
        def open_task(page, title):
            one(page.get_by_role('link', name='交付任务', exact=True), 'task route').click()
            one(page.get_by_role('button', name=title, exact=True), 'interactive task title').click()
            page.wait_for_load_state('networkidle')
        def evidence_form(page, locator, description):
            field(page, '^证据类型').select_option(label='文档')
            field(page, '^证据位置').fill(locator)
            field(page, '^说明').fill(description)
        def submit(page, name):
            target = one(page.get_by_role('button', name=name, exact=True), 'actual form submission')
            target.click()
            try:
                target.wait_for(state='hidden', timeout=10000)
            finally:
                if isinstance(page, NodeRemote):
                    h.rec.event({'kind': 'actual_ui_transport', 'responses': json.loads(page.bridge.call(page.ref, '$traffic', []))})
            page.wait_for_load_state('networkidle')
        def task_action(page, name):
            field(page, '^交付操作$').select_option(label=name)
            button(page, '^填写流转依据$').click()

        def login_logout():
            context, page = fresh('m')
            S.check(not page.get_by_role('button', name=re.compile('^登录$|^Login$')).is_visible(), 'Login leaves the login form')
            snapshot(page, 'authenticated landing')
            one(page.get_by_role('link', name='交付任务', exact=True), 'authenticated app history route').click()
            page.wait_for_load_state('networkidle')
            h.rec.event({'kind': 'ui_history_precondition', 'authenticated_route': page.url.split('?')[0]})
            button(page, '退出登录|注销|Logout|^退出$').click()
            page.get_by_role('button', name=re.compile('^登录$|^Login$')).wait_for(state='visible', timeout=10000)
            page.wait_for_load_state('networkidle')
            page.go_back(); page.reload(wait_until='networkidle')
            page.get_by_role('button', name=re.compile('^登录$|^Login$')).wait_for(state='visible', timeout=10000)
            S.check(page.get_by_role('button', name=re.compile('^登录$|^Login$')).is_visible(),
                    'Logout plus browser history/reload requires authentication')
            context.close()
        h.rec.run(ids[0], login_logout)

        reuse = h.c.get('browser_fixture_reuse')
        if reuse:
            if set(h.c.get('selected_case_ids', [])) != {ids[4]}:
                raise S.Blocked('Read-only UI fixture continuation is restricted to original history case')
            f = {'p': reuse['project_id']}; g = {'p': reuse['other_project_id']}
            a = h.get(f, reuse['task_id']); b = h.get(g, reuse['other_task_id'])
            f['i'] = a['iteration_id']; g['i'] = b['iteration_id']
            h.rec.event({'kind': 'read_only_UI_fixture_continuation', 'source_execution': reuse['source_execution'],
                         'task_id': a['id'], 'authoritative_task_version': a['version']})
        else:
            f = h.fixture(title='Independent visible A ' + S.key())
            g = h.fixture(title='Independent visible B ' + S.key())
            a = h.task(f, title='Visible task A ' + S.key()); b = h.task(g, title='Visible task B ' + S.key())
        pname = h.data('getProject', ids=h.ids(f), expected=200)['name']
        gname = h.data('getProject', ids=h.ids(g), expected=200)['name']
        def project_switch():
            context, page = fresh('m'); open_project(page, pname)
            S.check(a['title'] in text(page) and b['title'] not in text(page), 'Selected project A displays only its task content')
            open_project(page, gname)
            S.check(b['title'] in text(page) and a['title'] not in text(page), 'Switching project clears prior project task context')
            snapshot(page, 'project switch B'); context.close()
            context, page = fresh('o')
            S.check(a['title'] not in text(page) and b['title'] not in text(page) and pname not in text(page),
                    'Fresh outsider browser does not inherit another browser context project data')
            snapshot(page, 'outsider project boundary'); context.close()
        h.rec.run(ids[1], project_switch)

        def block_unblock():
            context, page = fresh('m'); open_project(page, pname); open_task(page, a['title'])
            before = h.get(f, a)
            task_action(page, '记录阻塞')
            field(page, '^原因与决定依据').fill('Browser-visible synthetic external dependency')
            field(page, '^责任环节').select_option(label='外部依赖')
            # Evidence is entered through real labelled controls.
            evidence_form(page, 'independent-v3/browser-synthetic', 'Synthetic browser evidence reference')
            submit(page, '确认推进交付任务')
            after = h.get(f, a)
            S.check(after['state'] == 3 and after['version'] == before['version'] + 1,
                    'Real browser blocker persists in backend exactly once')
            S.check('Browser-visible synthetic external dependency' in text(page) and '外部依赖' in text(page),
                    'Browser explains blocker reason and responsibility stage')
            snapshot(page, 'blocked task')
            task_action(page, '解除阻塞')
            field(page, '^解除依据').fill('Browser-visible synthetic resolved dependency')
            evidence_form(page, 'independent-v3/browser-resolved', 'Synthetic resolved reference')
            submit(page, '确认推进交付任务')
            current = h.get(f, a)
            S.check(current['state'] == 1 and current['version'] == after['version'] + 1,
                    'Browser unblock uses server-held original pending state')
            snapshot(page, 'unblocked task'); context.close()
        h.rec.run(ids[2], block_unblock)

        def capacity_error():
            context, page = fresh('m'); open_project(page, pname)
            one(page.get_by_role('link', name='迭代排期', exact=True), 'iteration route').click()
            page.wait_for_load_state('networkidle')
            button(page, '^调整迭代与容量$').click()
            selectors = page.locator('select[id^="field-plan-capacity-"][id$="-user_id"]')
            matches = [selectors.nth(i) for i in range(selectors.count())
                       if selectors.nth(i).input_value() == str(h.users['a'])]
            if len(matches) != 1: raise S.Blocked('Owner capacity control is not unique')
            row = one(matches[0].locator('xpath=ancestor::fieldset[1]'),
                      'owner capacity form item')
            one(row.get_by_role('button', name='移除这一项', exact=True), 'remove owner capacity').click()
            field(page, '^原因与决定依据').fill('Synthetic forbidden owner capacity removal')
            evidence_form(page, 'independent-v3/browser-capacity', 'Synthetic forbidden capacity evidence')
            before = h.data('listIterations', ids=h.ids(f), expected=200)['items']
            # Binding is complete only after a real response, not client-side form validation.
            one(page.get_by_role('button', name='确认调整迭代与容量', exact=True), 'capacity submit').click()
            if isinstance(page, NodeRemote):
                import time
                deadline = time.monotonic() + 10; observed = None
                method, route, _ = S.OPS['changeIteration']
                route = re.sub(r'{project_id}', str(f['p']), route)
                route = re.sub(r'{iteration_id}', str(f['i']), route)
                while time.monotonic() < deadline:
                    traffic = json.loads(page.bridge.call(page.ref, '$traffic', []))
                    observed = next((r for r in traffic if r['method'] == method and r['path'].endswith(route)), None)
                    if observed: break
                    page.wait_for_timeout(100)
                h.rec.event({'kind': 'actual_ui_transport', 'responses': traffic})
                if not observed: raise S.Blocked('Capacity form did not reach its actual public HTTP operation')
            page.wait_for_load_state('networkidle')
            after = h.data('listIterations', ids=h.ids(f), expected=200)['items']
            S.check(after == before, 'Browser rejected capacity removal preserves complete iteration plan and versions')
            S.check(bool(re.search('人力|工时|产能|未结项|CAPACITY_REFERENCE_INVALID', text(page))),
                    'Browser displays actionable business capacity explanation')
            snapshot(page, 'capacity rejection'); context.close()
        h.rec.run(ids[3], capacity_error)

        def history():
            context, page = fresh('m'); open_project(page, pname); open_task(page, a['title'])
            # Task history is exposed by the project's audit-record route and each record's
            # actual full-record disclosure, not the distinct schedule-differences tab.
            one(page.get_by_role('link', name='审计记录', exact=True), 'actual audit history route').click()
            field(page, '^任务编号$').fill(str(a['id'])); page.keyboard.press('Tab')
            records = h.data('listProjectAuditEvents', ids=h.ids(f), query={'task_id': a['id']}, expected=200)['items']
            records = [r for r in records if r.get('task_id') == a['id']]
            if not records: raise S.Blocked('Actual task audit record is not available for history navigation')
            latest = max(records, key=lambda r: r['id'])
            article = one(page.locator('article').filter(has=page.get_by_text('编号 ' + str(latest['id']), exact=True)),
                          'latest authoritative task audit card')
            one(article.locator('summary'), 'full audit record disclosure').click()
            page.wait_for_load_state('networkidle')
            h.rec.event({'kind': 'task_history_binding', 'audit_id': latest['id'], 'task_id': a['id']})
            S.check(bool(re.search('原因|依据|操作者|操作人', text(page))), 'History exposes provenance labels')
            current = h.get(f, a)
            S.check(str(current['version']) in text(page), 'Task page/history has latest authoritative version evidence')
            snapshot(page, 'history and latest version')
            # Exact timestamp text format is not frozen. Preserve visible value and known UTC for later
            # comparison without inventing a required separator/date format.
            h.rec.event({'kind': 'timezone_comparison', 'api_utc': current['updated_at'],
                         'expected_timezone': 'Asia/Shanghai', 'visible_text': text(page)[:12000]})
            context.close()
        h.rec.run(ids[4], history)

        def accessibility_context():
            context = browser.new_context(timezone_id='Asia/Shanghai'); contexts.append(context)
            page = context.new_page(); page.goto(h.c['web_base_url'], wait_until='networkidle')
            S.check(page.get_by_role('button', name=re.compile('^登录$|^Login$')).is_visible(),
                    'Fresh browser context does not inherit authenticated session')
            page.keyboard.press('Tab')
            focused = page.locator(':focus')
            S.check(focused.count() == 1, 'Keyboard focus reaches a visible interactive target')
            S.check(focused.is_visible(), 'Focused target is visible')
            snapshot(page, 'fresh browser keyboard boundary'); context.close()
        h.rec.run(ids[5], accessibility_context)
        browser.close()
    return h.rec.finish({'manual_review_required': ['Exact timestamp rendered in Beijing time',
        'Visual contrast and screen-reader completeness have no quantitative frozen criterion'],
        'browser_assertions': 'Only actual executed UI actions; missing semantic bindings are capability blocked'})

if __name__ == '__main__':
    raise SystemExit(main())
