# ROLE-backend-STAGE-PROBE-20261025-v1

作者执行者后端AI，非用户手改或独立验收。

实际root派工：实现tmp/810_latency_diagnosis最小开发诊断包，只本岗目录/报告不改产品；outerASGI ingress/bodydone/sync handler线程/send-end、SQLAlchemy只读events/checkoutwait/真实pool占用/threadCPU，原requestID映射不留body/binds/token，边界语义明确、不改响应/错误/线程。根16vCPU/32GiB Ubuntu22amd64、Docker29源935Python3.12镜像，7worker可阶段16、专用新DB max384，根管UI；不得碰云或旧13306/任意runtime凭据及独立805/809/814/817/818/829等，不看别岗日志、不扩agent。根随后给新可抛schema/3角色/20任务/serviceP1/privateenv，本岗先接口不猜ID。只指定backend/.venv跑owned stub/offline/SQLite，非SUTstub不冒SQL；根后续新环境实际1×20/40/400短诊断，正式400/600/270不降。10分钟先最小checkpoint，公开投递段≤18432字符可gzip/hash，随后真实失败/报告/log/handoff/commit/Issue。

执行改进：将pool_connect总时与QueuePool内部queue.get等待分开，避免把preping/建连算纯锁等待；threadCPU只同同步线程；ASGI仅消息透传不读payload，日志落盘/observer错误不能盖原错但诊断必须标INVALID。先因果桩/真实SQLite再交根容器，导入不启动/连库，关键源指纹与DB三重声明明确。
