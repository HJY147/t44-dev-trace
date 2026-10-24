# 定时调度完整应用模块报告

## 范围与依据
- 实际派工ROLE-scheduler-APPLICATION-v1；干净树FF合入12f7141026376763086e41a5b4db9ac1e82cfa33，保留基础与PR19。
- D001/D004和冻结v1已采用；只改本岗路径，未改BE/DB源码或共享锁，未读独立测试私有内容或联系testing。
- 当前已实现真实规则/门面/持久扫描/CLI；RabbitMQ网络、产品性能、独立验收与全产品规模达标未声明。

## 实际行为
- 唯一JSON改为冻结EscalationRule形状；解释器按显式起止/包含边界/priority/recipient_kinds处理可扩展规则数组。
- 默认只启用D001三级与60秒；保留UTC六位小数、1000/9999和elapsed差值，不用end+24h。
- API零参EscalationFacade()提供rules/list/create，返回冻结data；audit_id由Business.finalize在正确顺序补齐。
- create重验服务scope、state/expected_version/schedule_version/rule_version/窗口；不私自提交传入g的UoW。
- outbox(type2)+ledger+task版本/升级计数与Runtime审计/幂等快照同事务，存完整规则快照/原UTF8 SHA256。
- 硬键task/schedule/level，跨rule_version不绕去重；合法重复created=false不增计数/版本；savepoint无临时outbox孤儿。
- 快照owner与全部active经理，临期owner only；实际104收件人无截断。通知处理计数/投递状态从DB权威事件读取。
- Scanner使用真实Runtime.execute(Call,validate_call)；服务project_ids先认证，过滤范围且逐升级重验会话权限。
- ScanStore负责固定cutoff/keyset页/持久UUID/游标/心跳/计数；确定结果后前移，异常保留running。
- 提交后/游标前崩溃时按ledger原run UUID补计一次创建；UUID先规范化，避免大小写计数错。
- 周期恢复只筛当前原文hash的120秒旧心跳run（LIMIT前筛选，最多100）；不同规则历史不被偷偷重解释。
- python -m t44.scheduling为实际CLI，私密token文件、once/resume、单机flock、SIGTERM生命周期；无导入timer。

## 对接与边界
- 真实Call签名/Runtime顺序已读代码并获总协调确认；现有service-token CLI可用，未另造JWT/签发器。
- Issue3实际问取：https://github.com/HJY147/t44-dev-trace/issues/3#issuecomment-6360769538；消息岗确认broker只传稳定event标识。
- 扫描/HTTP与checkpoint是不同事务，不伪称原子；raw snapshot/hash在scan_runs及ledger保存，消息使用相同outbox.id。
- decided_by=1为冻结示例合成映射，不声称数据库ID1代表本人；正式部署须责任岗核对实际映射。
- D001阈值人采用与AI配置结构分开；原/新配置、时刻、影响、AI操作者见application-rule-change.json。
- 规则扩展真实diff：一个临时配置、解释模块0变更，最高priority生效；实验第四级未进入生产默认。
- 复杂度/运行命令见模块README；加载O(C+RlogR)，判定O(R)，DB/收件展开/并发网络成本没有冒称常数或实测达标。

## 执行与证据
- Python3.12.10，APScheduler3.11.3，按后端hash锁同步67包。原Ruff unused import失败保留；随后静态/Bandit通过。
- application-validation.log记录100→106→UUID边界修正后最终107 passed，17.49s，1条依赖弃用警告未隐藏。
- 107包含保留77基础、6扩展、2进程/凭据单测、22项真实MySQL8.4.11/ASGI-HTTP/CLI集成；非SQLite冒充实库。
- 真库测试前缀sch-*、只选t44_test，未清空其他模块数据；CI缺真实配置fail不skip，支持DATABASE_URL/T44_DATABASE。
- 真实20条全覆盖、重扫/进程突然退出后正式CLI恢复无重复，并发一202/一409、改期、终态/blocked均已实测。
- 真实MySQL1062/savepoint、写后验证失败回滚与拒绝审计、完整104收件人、冻结GET/202、规则版本不绕硬键已验证。
- application-coverage.json：仅scheduling的357语句/86分支综合83%，CLI子进程未汇入coverage；不是全局80%或验收。
- application-tests.xml为最终107项原始结果；application-ci-env.log保留系统python缺sqlalchemy编排失败与修正后真库1项。
- CI=1/URL入口1项在本机通过，非托管CI结果；无本机RabbitMQ网络、前端全链、400并发/P95或独立验收。

## 过程与交接
- 实际prompt原文/产物关系在本岗ROLE-scheduler-APPLICATION-v1.md；AI对AI“CLI尚缺”误判纠正未算用户识别或人工改码。
- WORKLOG/handoff及本岗日志/配置变更/diff同分支归档；更新现有draft PR19并交总协调按准确SHA审核，不自行通过/合并。
- 部署须配置真实服务会话、核对示例身份映射、单调度服务/共享锁路径；不同hash旧run须原配置恢复或运维审核处置。
- 整体代码规模当前已被总协调提醒超限，未改统计口径；后续真实去重重构与整产品复测由总协调组织。
