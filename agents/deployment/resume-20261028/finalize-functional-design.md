# P16封尾与新F实际身份：事前设计

root09:46Z要求仅本地准备小命令；本岗不执行云UI/服务。固定P16 gen02/resources/mirror及新F prepared binding，原1030/daaf不改、保盘保原证据。先S2/完整cohort结束才seal，不在负载中提前结束采集。

APP原resource seal/status给sealed全raw bytes/SHA；LOAD无额外finalize动作，原daemon在收齐finaltail时自动写mirror-final。新增小只读验证命令最多等45秒，核root从APP回传的bytes/SHA、mirror transport_complete/from_offset0、实际本地raw完整SHA及最后prefix marker、实际source/stream header，独占保存PUBLIC verified回执后原status/stop。APP看见LOAD完整证明后才stop资源，再按161f…保卷停P16。

新F仅prepared，使用root02 generation按be1975… arm/config/infra/migrate/idle；每步读真实clock，非stop/status须余窗≥600。原命令原件在新目录O_EXCL保存，不重seed或建业务数据。真实运行与身份提取分开记：只有实际6个基础角色Running/无重启，实际API source image/worker4/入口、TLS401/CA/hash、实际TTL都核后才输出running中性JSON；scheduler absent如实列。无真实PID/container数据就拒绝，不能填pending占位冒通过。

root明确仅允许读T15 PUBLIC schema f8fe6a…和一个6830B init PUBLIC JSONL ba480…，已核全SHA；不读792其他内容或root runtime其他文件。中性输出的sut_identity严格对应T15子schema，完整PRIVATE输入的账号/session/provider/root_grant由责任方另组装；本岗不补造它们。runtime_receipt先落盘hash后再写identity，避免自引用。prepared_receipt按T15固定ba480，CA de9b…，scope仅新F，旧P/P16/其他F不输入。
