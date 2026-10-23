# ROLE-database-POOL-DEFAULT-CANDIDATE-v1：真实派工

总协调实际派工；数据库AI执行，非学生亲改/本人研究。前一ABBA已FINAL；本任务独立分支/准确源CI，不回写原结论。

> ABBA FINAL已收到。开始新阶段：独立候选默认池配置，按root ac826cb9a788992297fe27d547bfcc208f83f1bc specs/changes/pool-retention-default-candidate-rfc.md +backend新445015f一页交接（可git show，勿合并无关worklog）先写设计/范围再实施。新codex/database-pool-default-candidate分支从当前root9307dab或更新稳定点，严格仅MySQLSettings默认5→15和10→0两常量业务变动；partial override size3应变3+0、双显式override保持，旧930硬5/10历史工具不能改凑绿。必要有意义的现有tmp/数据库测试新增按账本next869先向root报预留，生产source不可增无关逻辑。明确保留空闲上界30→90/标准6池峰90不变/partial峰会变、auth/锁/事务/超时/ping/LIFO不变。精确候选SHA分支PR，触发现有hosted完整CI一次（本地不发HTTP/SQL/压测），实际cloc核6307预期不变，CI前原本配置失败不可改写。与backend Issue3/4实际交接。不要合入root，不宣称正式性能过或生产准入。完成后FINAL交精确SHA/CI状态与交接，遇到CI技术问题自主窄修但勿绕门禁。

> DB e03 +backend445已root正常合入，当前root5408c05377d4f0084c6ae4eb596351add2004b67含完整ABBA与caller handoff，推荐新候选从此base，免后续不相关冲突。请实际读Issue4的6376569009并回应主要partialoverride/旧930/retained budget关注。

> 869已root账本正式预留，next868；仅你此阶段可用tmp/backend/persistence/869_pool_defaults.py。按设计推进，使用真实QueuePool+合成DBAPI有意义验证默认15+0/partial3+0/explicit保持+满池拒绝/返还保留/dispose，非只镜像常量断言。原993/930字节保持，hostedCI实际旧930是否被收集应说明而不修改，当前root新账本无需立即合并到候选可末尾只取所需元数据。

改进理由：已获两常量独立候选方向，但必须把partial override与保留成本、历史硬配置工具、准确新源CI/PR及证据分支分开；新回归验证真实QueuePool容量/保留/关闭，而非两常量自证或改旧预期。对应设计、engine.py两常量、root预留869及本岗原失败/CI/cloc/交接证据。
