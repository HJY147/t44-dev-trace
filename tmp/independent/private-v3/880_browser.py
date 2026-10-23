"""Actual isolated browser flows; no injected application state or mocked HTTP responses."""
import base64
import importlib.util
import json
from pathlib import Path
import re

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
        for cid in ids:
            h.rec.results.append({'id': cid, 'status': 'capability_blocked',
                                  'reason': 'Neutral runtime provides no Playwright/browser installation'})
        return h.rec.finish()
    h.setup_users()
    # UI vocabulary is derived from the frozen Chinese requirements, not a viewed candidate.
    # Missing/ambiguous semantic controls are navigation capability blocks, not invented defects.
    def one(locator, purpose):
        n = locator.count()
        if n != 1:
            raise S.Blocked('Frozen semantic UI navigation cannot uniquely bind ' + purpose + '; observed count=' + str(n))
        return locator
    def button(page, names):
        return one(page.get_by_role('button', name=re.compile(names)), names)
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
            page.goto(h.c['web_base_url'], wait_until='networkidle')
            field(page, '用户名|账号|Username').fill(h.credentials[actor]['username'])
            field(page, '密码|Password').fill(h.credentials[actor]['password'])
            button(page, '^登录$|^Login$').click()
            page.wait_for_load_state('networkidle')
            return context, page
        def open_project(page, name):
            match = page.get_by_text(name, exact=True)
            if match.count() == 1:
                match.click()
            else:
                selector = field(page, '^项目$|选择项目|Project')
                selector.click(); one(page.get_by_role('option', name=name, exact=True), 'project option').click()
            page.wait_for_load_state('networkidle')
        def open_task(page, title):
            one(page.get_by_text(title, exact=True), 'task title').click()
            page.wait_for_load_state('networkidle')

        def login_logout():
            context, page = fresh('m')
            S.check(not page.get_by_role('button', name=re.compile('^登录$|^Login$')).is_visible(), 'Login leaves the login form')
            snapshot(page, 'authenticated landing')
            button(page, '退出登录|注销|Logout').click(); page.wait_for_load_state('networkidle')
            page.go_back(); page.reload(wait_until='networkidle')
            S.check(page.get_by_role('button', name=re.compile('^登录$|^Login$')).is_visible(),
                    'Logout plus browser history/reload requires authentication')
            context.close()
        h.rec.run(ids[0], login_logout)

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
            button(page, '^阻塞$|标记阻塞|进入阻塞').click()
            field(page, '阻塞原因|^原因$').fill('Browser-visible synthetic external dependency')
            field(page, '责任环节').click()
            one(page.get_by_role('option', name=re.compile('外部依赖')), 'external dependency stage').click()
            # Evidence is a real UI-entered reference, not an injected API payload.
            field(page, '证据.*位置|证据.*引用|locator').fill('independent-v3/browser-synthetic')
            ds = page.get_by_label(re.compile('证据.*说明|证据.*描述'))
            if ds.count() == 1: ds.fill('Synthetic browser evidence reference')
            button(page, '^确认$|^保存$|^提交$').click(); page.wait_for_load_state('networkidle')
            after = h.get(f, a)
            S.check(after['state'] == 3 and after['version'] == before['version'] + 1,
                    'Real browser blocker persists in backend exactly once')
            S.check('Browser-visible synthetic external dependency' in text(page) and '外部依赖' in text(page),
                    'Browser explains blocker reason and responsibility stage')
            snapshot(page, 'blocked task')
            button(page, '解除阻塞').click()
            field(page, '解除依据|^依据$').fill('Browser-visible synthetic resolved dependency')
            field(page, '证据.*位置|证据.*引用|locator').fill('independent-v3/browser-resolved')
            ds = page.get_by_label(re.compile('证据.*说明|证据.*描述'))
            if ds.count() == 1: ds.fill('Synthetic resolved reference')
            button(page, '^确认$|^保存$|^提交$').click(); page.wait_for_load_state('networkidle')
            current = h.get(f, a)
            S.check(current['state'] == 1 and current['version'] == after['version'] + 1,
                    'Browser unblock uses server-held original pending state')
            snapshot(page, 'unblocked task'); context.close()
        h.rec.run(ids[2], block_unblock)

        def capacity_error():
            context, page = fresh('m'); open_project(page, pname)
            button(page, '迭代|人力安排|产能').click(); page.wait_for_load_state('networkidle')
            button(page, '修改计划|编辑迭代|调整人力').click()
            owner_name = 'Synthetic a'
            row = one(page.get_by_role('row').filter(has_text=owner_name), 'owner capacity row')
            one(row.get_by_role('button', name=re.compile('删除|移除')), 'remove owner capacity').click()
            field(page, '变更原因|^原因$').fill('Synthetic forbidden owner capacity removal')
            field(page, '证据.*位置|证据.*引用|locator').fill('independent-v3/browser-capacity')
            before = h.data('listIterations', ids=h.ids(f), expected=200)['items']
            button(page, '^确认$|^保存$|^提交$').click(); page.wait_for_load_state('networkidle')
            after = h.data('listIterations', ids=h.ids(f), expected=200)['items']
            S.check(after == before, 'Browser rejected capacity removal preserves complete iteration plan and versions')
            S.check(bool(re.search('人力|工时|产能|未结项|CAPACITY_REFERENCE_INVALID', text(page))),
                    'Browser displays actionable business capacity explanation')
            snapshot(page, 'capacity rejection'); context.close()
        h.rec.run(ids[3], capacity_error)

        def history():
            context, page = fresh('m'); open_project(page, pname); open_task(page, a['title'])
            button(page, '历史|审计|流转记录').click(); page.wait_for_load_state('networkidle')
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
