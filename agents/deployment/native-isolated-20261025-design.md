# 2026-10-25 原生隔离功能部署设计

部署AI，先设计再执行。SUT唯一`ade5e4c1998b4c2f014afde8c011645c6c5a7412`，不是当前工具分支或旧bc5应用。用途为上下文隔离功能/故障验收环境，不是云性能证明。最晚2026-10-25T08:50:00Z开始前已完成本轮进程停止；守护在08:48先正常停止，08:50前核拥有权后强停仍存活的本岗进程。机器旧MySQL127.0.0.1:13306/PID7980及其他服务/库/账户不改动、不发信号。

先检查新API18096、Rabbit25696、EPMD24396、distribution35696、CLI45696–45705回环端口可bind；占用则不操作占用者，记录后另选新明确端口。broker复用ade5公开runtime.py的完整拥有权/私有Cookie/CLI/关闭逻辑，仅派生新端口常量副本并记录原SHA、新SHA、精确差量；原文件不修改。全新0700运行目录、Cookie、user、vhost及独占日志/state，没有管理插件和公网监听。原控制器不使用HOME内cookie，保持nocookie+显式0600文件前置setter；不沿用任何旧run的HOME或秘密，不修改用户HOME环境。

本轮控制器只在新`.agent-worktrees/.runtime/native-isolated-20261025/<uuid>`写入。部署依赖从已准入native-mq layout的固定OTP/Rabbit路径取得；Python只复用已存在原生依赖，核ade5锁SHA、实际distribution清单与uv pip check，执行文件和入口/锁/源hash写build manifest。只导出Git中明确的backend/t44、backend/requirements.lock、backend/pyproject.toml，不导出或读取tmp/829/839/841/852任何内容；清单明确是运行源子集，提供准确commit/tree OID，不能声称全仓checkout。

证书用现有OpenSSL生成全新私有CA及localhost/127.0.0.1 SAN叶证书，校签名/用途/SAN/有效期/keypair。Uvicorn原生TLS，API仅127.0.0.1:18096/4worker/no-access-log/no-proxy-headers。请求ready只用既有非破坏接口未鉴权状态作连通观测，不猜验收用例；不预置项目、ID、用户或业务数据。

root稍后指定仅新库的0600appenv，部署岗拒绝admin.json和未经明确准入的任何环境。只校DATABASE_URL为mysql+pymysql、127.0.0.1:13306及root显式新database名（与T44_DATABASE相同），不输出DSN或密码。新AMQP来自本轮0600secret JSON；API、consumer、scheduler只注入明确必要环境。consumer入口python -m t44.messaging。scheduler等待root提供fresh、正确scope和到期足够的0600token文件后再启动python -m t44.scheduling；不自行猜ID、签发或续命。锁文件本轮专有，规则保持源60秒。

每个自有进程用新session启动，登记PID、PGID、UID、lstart、argv指纹、cwd和角色；停止前重新逐项比对，拒绝未知或复用PID。API监督进程与已证明为其子进程的worker单独登记，不能广域遍历/杀进程。另有独立deadline guardian和10秒资源采样，只读本轮登记进程的ps CPU/RSS/elapsed及非原子UTC/monotonic anchor；不读旧进程环境/业务数据。guardian先停scheduler/consumer/API，再通过本轮Rabbit官方shutdown与EPMD空节点检查停机；超时只对仍匹配自有identity的PID/PGID强停，false/部分结果原样保留。watchdog不依赖聊天继续采样，进程被外部中断时资源停止是否完成仍须实际后验。

准备和启动分段：先准确源/依赖/证书/端口/新broker与guardian；DB未知时不启动业务。root审manifest与本轮broker私有文件路径，再追加新DB环境。为独立验收只由root选取中性manifest/CA/API地址/生命周期入口，不传部署内部记录或私有用例。新前缀824合成测试只验证本岗隔离/时间/拥有权/计划门禁；实际broker readiness不等于独立验收。每阶段保留真实失败、原始私密输出与安全公开回执，Git/Issue7与prompt归档延续。
