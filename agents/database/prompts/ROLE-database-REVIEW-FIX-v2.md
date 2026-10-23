# ROLE-database-REVIEW-FIX-v2：本轮实际派工

来源：总协调实际消息；AI执行修复，不记作用户亲自改码。

> ROLE-database-REVIEW-FIX-v2：恢复固定DB岗，续你3ed未验证checkpoint。当前同机安静窗口仍在（后续契约/升级各600秒，root未宣布结束），本机严禁pytest/MySQL迁移/seed/HTTP/构建；可读远端GHA失败日志并修复、push让托管CI真验证。3ed的39938428158/39938417442 product失败，请先取原始日志确认原因（别猜、不削弱956/旧断言/957）。root尚未合3ed。已有新空t44_review，待窗口后仍要真实 controlled schema变更/恢复验证；不能用mock或托管单测代替。请本轮保留失败→改动→远端结果证据，并在等待CI时实施/评估真正seed受信row-builder/默认字段等消重复，维持40/6000/9000/15000数据和manifest/7态/证据语义，禁止压行/改计数/搬业务到配置。BE已合创建/会话发行复用等静态净减112且CI317全绿，FE真删83仍不足规模目标；你的C-P4新增也应如实统计，无强行保证填满缺口。956路径tmp/backend/persistence/956_schema_semantics.py已独占，下一个955；新必需测试先报备，原测试可增强。明确tag本轮新增派工/prompt，正常自己worktree/PR17/Issue4。先修正确性，拿可核对checkpoint再交接。

改进理由：先读真实失败而非猜测；最小修复保留安全门禁；CI、Inspector夹具、专库实际漂移恢复分开记录。seed只做有等价依据的构造逻辑去重，不改变业务或统计政策。
