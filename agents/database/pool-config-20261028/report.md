# 显式连接池配置：本地完成，待根审核/CI

AI数据库岗；backend已委托并确认接口。Prompt-Ref: ROLE-database-POOL-CONFIG-20261028-v1，实际派工/确认见 prompt.md。基线 **b9847f8a946a310b90e8fb228a0e5c1061612e13**，先行设计 **fb5d622dfd16de30dbde9676c295cc36715c275f**，精确产品/测试源 **92cf5c108ee549b35dda6d775e0357ded9e40743**；分支 `codex/database-pool-config-20261028`。

只在 `Settings.mysql_settings()` 原 MySQLSettings 构造中新增两个参数：

| 环境变量 | 无变量时的原默认 | 输入与拒绝 |
| --- | --- | --- |
| T44_DB_POOL_SIZE | 5 | int转换；原MySQLSettings继续要求正整数 |
| T44_DB_MAX_OVERFLOW | 10 | int转换；原MySQLSettings继续要求非负整数，0合法 |

任一显式变量只覆盖对应字段；空串、非整数、浮点文字、True/科学计数文字均拒绝，不能静默回退。使用原有风格的 Python int 转换，因此可接受空白或加号包围的合法整数字符串。转换发生在 mysql_settings()，不新增 Settings 字段、不在 from_env() 提前读取新变量；DATABASE_URL仍从Settings实例读取，TTL和其他字段来源不变。原driver/显式数据库/T44_DATABASE匹配检查仍先于新转换；转换后的数值边界及全部原timeout/port/identifier/credential校验由原MySQLSettings执行。已有engine不会因为随后改变环境变量而自动重配。

## 实际验证和计数

Python3.12.10、SQLAlchemy2.1.6、pytest9.1.1、Ruff0.17.2、Bandit1.9.4；复用只读已有解释器，PYTHONPATH指向新独立树，禁止写bytecode/pytest cache。新测试仅在根预留的 `tmp/786_database_pool_20261028/786_pool_settings.py`；原测试未改。

- 设计先提交。原准确b984源码上，显式容量目标5项实跑 **4 failed、1 passed、26 deselected**：A5/10本就满足，其余仍返回5/10；旧红日志/JUnit保留，不是环境失败。
- 两行实施后，新配置契约 **31项** 加原目标回归 **7项**，合计 **38 passed / 0.26s**，无失败/错误/跳过。覆盖所有默认字段逐值、单变量、A5/10/B15/0/C20/0/5/0、非法文本/范围、原URL与数据库声明错误优先、原DATABASE_URL/TTL来源、ENV读取时点；经原create_mysql_engine核实际QueuePool容量/overflow、脱敏、session初始化hook及RC，最后dispose。新模块全过程mock阻止并断言PyMySQL connect零次。原目标覆盖850配置解析/目标守卫、993 lazy engine/会话初始化/故障脱敏，不执行HTTP或MySQL。
- 限定CI同配置Ruff、限定Settings Bandit通过；产品/测试源码及说明限定diff-check通过。封档整包check因原pytest红log/XML的8处尾空格真实exit2，raw-diff-check.json保留原诊断；原失败证据不修剪，整包check不宣称通过。原四项失败没有删断言或降门禁。
- 原固定cloc2.10对design fb5d（应用与b984全同）实测 **5933**，对精确92cf实测 **5935**；只有settings.py有效行 **+2**，其他应用逐文件计数相同。`--require-range` 两次均exit1；候选仍超5100上限 **835**，strictLOC门禁未过。

boundaries.json绑定仅Settings两行增加；persistence整个目录、Rows旧默认tuple(t.c)、SQL/事务/鉴权/API/资源/specs/原tests/CI/计数器Git对象均同b984。未自动携带select(table)候选82e92；两个候选分别审核/准入。

## 后续实验设计与准入

这里只做整数预算，没有查询或修改任何MySQL设置，没有启动连接池负载：

| 未来方案 | API进程数 | 每进程(pool_size, max_overflow) | API连接上限 | 加预留64 |
| --- | ---: | --- | ---: | ---: |
| A | 16 | 5,10 | 240 | 304 |
| B | 16 | 15,0 | 240 | 304 |
| C | 16 | 20,0 | 320 | 384 |
| 64worker另案 | 64 | 5,0 | 320 | 384 |

A/B相同最大连接240，可另以同负载隔离保留池/连接churn；它们尚未运行。C和64worker案必须在新目标实际查询MySQL max_connections、核当前所有角色/连接预算和预留后才准入；旧配置384只作历史约束，不能当新实例读回。16×25/0已400再加其他角色，64×默认(5+10)达960，均不能默认采用。400客户端协议与物理连接预算分别保留，不改变严格验收条件。

本岗未连接原生MySQL/旧tmp796/原tmp794/792私件，未跑SUT/HTTP/云/负载/性能，未使用费用授权购买或部署。根独立审核、组合CI/覆盖率、新目标实际连接预算与后续正式协议由根调度。配置通道可用不等于性能改善、正式性能通过或strictLOC通过；学生研究正文未写，AI操作不记为用户亲改。
