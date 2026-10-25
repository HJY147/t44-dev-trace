# 801 新诊断 P 准备/短窗工具交接

本岗AI先写design.md，再草稿4fa1051f，最终工具C f811c5c1cc4573ab57db1be35fa1e9ade379d7cf。
没有产品源码、契约、SQL/锁、正式压力工具或独立材料变更。零新产品行，未作新
cloc或性能通过声明。当前真实云执行仍归根，根读凭据/启动，子岗没有云/旧13306
或任意实际私密凭据访问。

最小两步接口已交根与部署：810无需业务packet，可先启动；801准备器后读根显式
accounts，用真实原CLI+登录/DB/HTTP生成私包，load driver只读该私包。stage module
原b767/SHA8f0dbec…不变，prepared400slots供后续1/20/40/400短窗，正式验收独立。
细节在runbook.md，精确两源hash/长度/压缩往返见delivery-receipt.json。

本地最终13目标绿，0fail/error/skip，1.45s，FastAPI已存在TestClient弃用警告保留。
目标包含：import无产品/线程/网络；TLS精确target四拒；0600/UID/原子保留/拒symlink；
精确新库/近似/旧P816/13306/root四拒；失败/过期/重合task私包拒；自owned HTTP
transport stub strictCA/连接复用/reset不重试；SQLite真实源935 seed40projects/400
tasks/400edges/600records，原CLI服务令牌实际40IDs、三真实API登录、两实际提醒
create/dedup对，两次四路径请求连续BLOCK→UNBLOCK/version各+1，再真实提交后
模拟断连使私包不可续跑，实际DB version已+3但私包保留旧值且resumablefalse。
此test-only缩小数据与TestClient桥不冒真实MySQL/TLS/云400并发。

第一轮12目标1红11绿，失败仅测试预设提醒201，实际冻结202；保留checks.initial.*。
修为精确202并增加transport目标后13绿1.12s；同13又加入commit-then-disconnect
因果断言，最终13绿1.45s，不累计成26。首草稿Ruff7项非零后仍commit的过程已记录，
随后修未用变量/capture_output，并以逐行noqa说明宽异常仅用于匿名失败/DSN脱敏；
新checks首PLW1510显式check后修，插入测试误把packet三断言移到另一test的F821
在执行前修复。最终Ruff/format/diff-check绿，早期失败不改写成通过。

私包只含sessions/TTL/真实taskIDs/version/规则/事件/scanUUID，没有原password或
DB DSN。所有输出O_EXCL|O_NOFOLLOW0600固定fd，原状态提交保留不回滚。
短窗无重试，任一异常client停止、保留匿名类；已提交但失响应时不可盲重用packet。
成功数/分位含失败并分开状态；deadline不等于持续并发证明，writer批量末写不复刻
正式工具背压，成功connect统计也不能证明TLS全部尝试或网络根因。

下一步是根审核该精确工具/私密账号shape，实际新MySQL/原CA环境prepare，然后
根统一短窗与stage资源采样；出现首实际失败先保留状态再修，不自动重seed、不改
frozen正式断言/鉴权/事务或cap。最终400/600/270、0错误、发布与成本资源状态仍未
由本工具证明。本报告为AI开发记录，非学生手写研究报告。


根追加准入后最终C更新 f811c5c1cc4573ab57db1be35fa1e9ade379d7cf：只读profile在
任何CLI/登录/业务写前落盘，inspect-only核实际数，不足400可slots1/40；调用没有
创建session文件。最终13目标1.45s绿，覆盖SQLite40候选对400请求不足但0业务写。
profile初版13绿1.25s后代码审发现inspect传0会把requested/sufficient显示不准确，
执行前改为保留原请求400与独立inspect分支；中间13绿再细化writes_started标记，
最终同13不累计。旧fe197代码/包仅历史，现公包12643/install13724字符，owned实际
展开逐字对比通过。真实6000seed400候选NP，静态600算法性质与实库观测分列。

封档追加：dab62E staged diff-check发现原pytest traceback/log/XML的16处原始尾空格，命令非零但后续commit仍执行，不能记该次green。随后不strip原证据，原bytes保留dab62历史/ignored本地copy与lossless gzip，raw/gzip双SHA+roundtrip在raw-artifact-manifest.json；当前封档重新检查，无业务/脚本变更。
