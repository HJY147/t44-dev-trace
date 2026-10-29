Agent-Role: backend
Prompt-Ref: ROLE-backend-DEPENDENCY-CI-FIX-v1

准确5cc首次CI failure已实际读取并保留：run40087756354，coverage job120854051910及contracts120854052090，官方metadata head_sha=5cc856d6fa94b1fdde32605543b53822f9747f00；不是依据本地绿推CI绿。唯一失败是985真实MySQL账本block实际(20SELECT,5DML,2control)对旧(22,5,2)，unblock实际(22,5,2)对旧(24,5,2)，正好对应原guard-specific方案少两SELECT。原全suite560pass2fail，contract177pass2fail/integration91pass2fail彼此重叠；原日志两gzip双hash/解压核验，不rerun旧run、不覆盖失败。

先847256e范围、32cb991设计，已提交test-only source ead155e6204de9004bc968e9b9648358cfed75f8。相对5cc生产零差异；985仅两精确SELECT常量22→20/24→22和一条历史注释更正。AST白名单其余全部节点相同，原DML/control/auth/Tx/RC/独立审计/幂等/ACK不明断言保留；不是把精确数改成范围或删断言，更不改变270ms/600秒/零错误门槛。

旧失败前端点200/schema及打印2UoW/2acquire/2commit成立，但后续auth/closed/replayed断言位于失败位置之后，两case未执行，不冒称已有完整通过。新自然product40088982094已绑定ead155e，首次in_progress，需实际全CI证明。原PR44仍固定5cc代码审核范围，新的测试差量需单独核；本轮原backend Ruff/format绿，collect-only仅收集5个参数，不当5pass，不本地重跑MySQL/原36绿/云/服务/负载。

报告及精确原件：agents/backend/performance-repair-839-ci-fix/report.md、design.md、raw-manifest.json、test-only-proof.json、candidate-binding.json。应用与5cc逐字同，规模仍6316/超1216（沿原准确测量+字节身份，未新cloc），无规模或性能通过。没有读取独立839私有材料或向其发送开发信息；作者/修正为后端AI，不是人类改码。
