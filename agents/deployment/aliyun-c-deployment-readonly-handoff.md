# 准确C版本最短部署路径：只读交接

应用精确C：`0dfb55c2191200d947c5423fd9ee74bb0812cc5a`，由本地Git解析核对。本文只读该提交的`deployment/README.md`、`compose.yaml`、`deployment/ops.py`，没有执行部署命令。既有Docker完整构建/Compose/恢复的历史证明绑定`31f4dff935973162544951fe0660ce208edb7007`，不能冒称C已在新云机验证。

现有Linux单机Compose入口已经实现，最短顺序（下述为后续操作路径，非本轮执行结果）：

1. 在应用机取得准确C完整仓库，具备Python3.12、Docker Engine及支持`up --wait`的Compose v2，固定镜像/锁依赖能下载。
2. 仓库根执行`python3 deployment/ops.py init-env`，再`config-check`、`build`、`infra`。随机`.env`为0600并拒绝覆盖；不能公开完整Compose解析值。
3. `python3 deployment/ops.py migrate --database t44`先看计划，再加`--execute`实际迁移明确项目库。初始化账号走`ops.py account init-user --username NAME --display-name NAME`交互口令输入。
4. 空合成库用`ops.py seed-demo --database t44`，C默认40项目/6000任务/9000依赖/15000记录；或者先启动api/consumer/web创建项目。以实际返回/已建项目取得ID，不猜ID或复制旧环境状态。
5. `ops.py scheduler-token --project-id REAL_ID`（多个项目重复参数）签发scope，再`ops.py start`、`status`。API4worker、consumer和scheduler独立；Token目录只读挂载与flock卷已接线。默认会话TTL3600秒，若跨过期时间须到期前显式受控`--rotate`，现有工具没有自动续签。
6. 实际核验新云机镜像构建、进程/数据库/队列/调度和页面/鉴权入口。默认web只监听宿主127.0.0.1:8080、DB/MQ无宿主端口；管理可用SSH隧道，跨机发压还需另审受限私网入口，仅允许发压机来源，不能直接把loopback当跨机已可达。

截至root后续UI转述，load实际详情与17:00释放配置已回查，两台同VPC/交换机且计费中；实际释放仍待到期核实。凭据之外尚缺：两机可用管理连接/实际私网连通；Docker/Compose及Python3.12是否已安装、固定镜像和Python/Node依赖在杭州能否及时下载；准确C实际云构建/迁移/启动与版本/镜像摘要取证；预算内的证据导出和释放核实安排。当前没有把上述前提假称完成。正式复测方法/用例/fixture与结论由责任岗另行冻结、执行，本岗不访问其私有资料。
