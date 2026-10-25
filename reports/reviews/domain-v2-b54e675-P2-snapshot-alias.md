# 内部域v2原候选：V2-SNAPSHOT-ALIAS-01阻断

## 1. 精确范围

产品a07ad028a8efad4ecd186246bf2b7935c361b117、证据HEAD b54e6757cdf1eed72adf4eaea68d8ae0c34c42ca，对照e45a2b980c6ba8c61761f897414d54a10000409d/product935。总协调已授权内部API v2移除Command/Gate/Cycle桥，不能因此删外部规则。本稿仅原候选拒绝记录，后续修复另稿，不追改本结论。只产品/公开开发证据，不接触tmp809/814/817/818/829独立材料、实际成绩或keys，不开新agent。

## 2. 实际阻断

P2 V2-SNAPSHOT-ALIAS-01：原models.py:80对row仅MappingProxyType(dict(row))浅拷贝，assessment.review_evidence仍保留合法caller list；state_machine.py:124实际消费其bool。冻结Transition可因调用方在构造后append/clear改变同一上下文的DELIVER决策。它违反本轮不可变已验证snapshot边界；不是已证明REST越权或真实数据库race，当前同步facade无await也不扩展为生产可利用并发结论。

## 3. 一次最小反例

先probe-design后新tmp/808_review_domain_v2/808_snapshot_alias_probe.py，绑定原models/state_machine hash，用批准的backend Python一次exit0捕获两方向：空list构造→EVIDENCE_REQUIRED，调用者append→同context返回state6；非空list构造→state6，caller clear→同context变EVIDENCE_REQUIRED。alias=true。全为自造有效manager/当前评估/代码评审pure映射，无旧oracle、socket/HTTP/DB、OS调钟或产品编辑。结构化记录忠实转录实际工具stdout，不冒原stdout bytes hash。exit0表示反例捕获，不表示候选绿。

## 4. 其余静态核对

17产品hash同精确stage/E，旧commands删除；API、两OpenAPI、需求/业务规则同base。16个Runtime/Call关键函数AST同；locked_scope/authenticate/member查询经trusted Call.members封装，原project/user/active过滤、排序/锁参数保持，新增resource/insert helper只收固定表/列及既有受验证路径，非request选择器。session刷新、项目/成员/任务锁序、幂等重放、CAS/独立拒审计外围未见新弱化。ErrorCode从契约加载时tuple截取并以固定order SHA拒漂移，保留原1–41身份；纯域patch含原批准清理、周期推进和record_type，facade保留版本/assessment前置、D008及rework容量检查次序。

## 5. 开发证据边界

XML实复算170域/143原HTTP零失败，170按91真实v2旧行为+15历史constructor-only+63新边界+1个57120差分记，不把15当v2安全证据。差分通过fixture映射比较纯decision/target/effects/violation，非所有patch字段/外部DB证明；新63只测顶层dict变更，未覆盖此次nested list alias。生产静态无tmp/oracle import，owner fresh app+START阻断imports/连接只证明其该小scope。微基准是数微秒bridge/纯域CPU，不是HTTP/400×600验收。

## 6. 计量与未验证

固定cloc2.10回执scope18→17文件、2363→1987净376，含新helper与原commands。未重新全产品计数，6335-376=5959只是投影仍超5100；a19 checkpoint并非完整绿绑定，139旧误绑定已纠正。本岗不重跑170/143/差分/微基准，无MySQL/CI/独立/正式性能。root收到P2后派作者修复，不由审核岗代写产品。

## 7. 十项判定

|项|判定|
|---|---|
|1 source/E|17hash匹配|
|2 内部API授权|允许v2，无兼容桥要求|
|3 外部契约|byte同base|
|4 规则/patch/CAS|静态无其它新增阻断|
|5 snapshot|P2失败，合法list别名可变|
|6 身份/锁/epoch|原顺序/刷新保持，非MySQL实证|
|7 ErrorCode|身份锁定，非显示序号重映射|
|8 开发测试|170/143仅其scope，15constructor分开|
|9 大小/性能|净376非全局达标/正式性能|
|10 集成|原a07/b54不准入，待新精确修复|

## 8. 结论

原a07/b54因该P2暂拒集成；最小修复应在原list/tuple验证后独立冻结实际消费的review_evidence成员序列或标量，保持guard先后、不增加旧桥。原证据/probe保留，后续新source窄复审另记。无APPROVE/global/main/产品通过。
