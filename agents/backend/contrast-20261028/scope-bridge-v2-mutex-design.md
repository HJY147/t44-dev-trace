# Scope桥v2：与v4统一phase操作锁

后端AI，ROLE-backend-SCOPE-BRIDGE-V2-MUTEX，2026-10-28。root新派发共享互斥契约后，v1源码/manifest/34+9离线证据封存于447f611f，不能对v4运行。v2另新目录 `tmp/790_backend_contrast_20261028/scope-callback-bridge-v2-mutex`、新manifest和安装目的路径，原失败与v1不回写。没有新云/SUT授权执行。

部署岗责任文件 `deployment/cloud-reuse/v4/mysql-budget.py` 是仅Python3.10 stdlib的公共依赖；派生器放入每个新F `<phase-dir>/mysql-budget.py` 并在 `binding.file_hashes` 记录其SHA。后端不复制、不修改部署岗文件；每次先按实际binding核文件SHA，再用importlib只载这个精确文件。

I/O：`mysql_budget.operation_lock(Path(phase_dir), actual_binding_sha256, timeout_seconds)` 返回同步context manager。锁固定 `.v4-operation.lock`，root:root0600、no-follow/close-on-exec、regular/inode/mode核验；EX|NB每50ms重试，最多10秒，参数上限30，0可立即试，退出关FD释放。后端锁等待取min(10,桥剩余deadline)，锁后/SQL前再核deadline；timeout保原拒绝，不自动retry。两个直接SQL阶段分别为preflight（实际project/iteration归属）与seal（原authstore真实credential digest/exact scope），各自一次独立持锁；原GEN scheduler-token/rotate/start调用必须在锁外，由GEN自取同一锁，禁止父桥跨GEN持有锁。

验证：先留v1未取共享锁的无SUT红例；注入一个真实flock测试锁，实际本地子进程能在原GEN调用时取得相同锁而在SQL时被拒绝；覆盖SQL异常仍释放、锁等待timeout未发SQL、剩余deadline限制锁等待、依赖SHA变化在导入前拒绝。保原34桥检查，不删assert，不改120/600/lease/scope/wire。部署锁自己的root模式/跨进程争用由责任岗自测，后端只证明接口正确衔接；实际Linux双机/MySQL并发预算仍待下一窗口。
