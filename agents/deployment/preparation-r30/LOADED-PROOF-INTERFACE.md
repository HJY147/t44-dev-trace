# R30 loaded 中性证明接口（供root转交，不联系QA）

本页是路径/schema/命令约定；当前没有真实APP加载证明文件或其hash。CI文件探针不充当loaded证明。两份官方原始manifest保持原字节：

| 角色 | 原始绝对路径 | SHA256 |
|---|---|---|
| source | `/Users/yang/Desktop/nothing/软件开发大作业/.agent-worktrees/deployment-preparation-r30/tmp/761_deployment_preparation_r30/official-artifact-12880320744/source-manifest.json` | `0c5b0c0e027578b0f62711175beac4680aab8331bfbc4af2547f02398f38cc1b` |
| backend bundle | `/Users/yang/Desktop/nothing/软件开发大作业/.agent-worktrees/deployment-preparation-r30/tmp/761_deployment_preparation_r30/official-artifact-12880320744/backend-bundle-manifest.json` | `b2db2e1c5cf56fa5df4f20f7003d44d6b3b9ab4cd484b45d921c82640295d345` |

QA中性adapter只需这两manifest和未来真实loaded proof，无须读其相邻源/镜像、部署日志或任何凭据。

当前R30-NEUTRAL-RECEIPT-03修复后，现有 `r30-window.py import-backend --receipt <new PUBLIC json path>` 只有在backend实际验证成功后，才排他写 `r30-backend-import-receipt-v1`。原receipt本身保留完整60行raw观察，不再补跑第二次探针。旧候选字符串格式只保留历史，不重写云原件或包装旧字符串。

建议新云路径：`/root/t44-r30/<new-run>/backend-import-receipt.PUBLIC.json`。路径只是约定，本岗没有创建真实APP proof；root在实际import成功后直接核原文件bytes/SHA并交中性adapter，不另重建receipt：

```bash
python3 "$R30_PROFILE/r30-window.py" import-backend \
  --package "$R30_PACKAGE" \
  --manifest-sha256 b2db2e1c5cf56fa5df4f20f7003d44d6b3b9ab4cd484b45d921c82640295d345 \
  --receipt "$R30_HOSTROOT/backend-import-receipt.PUBLIC.json"
sha256sum "$R30_HOSTROOT/backend-import-receipt.PUBLIC.json"
```

原始receipt字段仍为kind/source_sha/bundle_manifest_sha256/source_manifest_sha256/identity/full_runtime_files/package_resolution/business_services_started/volumes_modified。`package_resolution`现在**原样等于backend真实observed字典**：uid、package_origin、python_version、sys_executable、business_env_absent、files；完整files有60行path/bytes/sha256/mode，full_runtime_files取真实len(files)，不是源条数推算。identity继续保存Docker29实际descriptor→保存config→layers/DiffID的原证明，config与actual_id不要求字符串相等。v1 kind和已发布expected-shape语义不变。

backend在返回observed前已验证全部60运行文件（含完整53backend）与官方source manifest去掉两Dockerfile后的完整bytes/hash/mode集合相等、UID10001、`find_spec('t44').origin=/app/backend/t44/__init__.py`及业务环境缺失。它没有import业务应用、派HTTP或启动业务。原receipt不含账号、令牌或Env值；CI文件表不能代替这份实际APP观察。

root交接只给原receipt bytes、原路径、实际bytes/SHA与观察时间。已公开adapter694fc3纯validate只确认其声明范围内的structure/raw SHA绑定；root仍负责完整source/base/config/layer/运行来源链复核，不能把结构通过变成SUT验收。任意缺项/错hash/旧字符串拒绝，绝不为了接收而修改QA类型或重写原receipt。实际新profile必须经root准确commit复审并重新派生pin链。

## APP服务角色与scheduler状态

- 每phase配置的PERSISTENT七角色：`mysql,rabbitmq,api,consumer,scheduler,web,tls-gateway`。这是资源枚举，不是镜像件数或实际运行数。
- `infra`只启动mysql/rabbitmq两常驻角色；`idle`再启api/consumer/web/tls-gateway，预期六个常驻，scheduler仍未启动。
- scheduler必须精确项目scope的真实服务token以及显式`scheduler-start`后才是第七个；不可按镜像已存在或配置已生成就记scheduler running。
- operations profile的`migrate,admin,credential-admin`是一次性容器；不计入PERSISTENT常驻数。resource collector/systemd observer是外部观测进程，另列。
- F/P是两个隔离phase，各有七角色枚举；本轮只按root准入phase依次运行，不把未启动phase计入实际资源。最终实际数量/角色/scheduler状态由新status的逐资源state.Running/absent和真实unit/PID证据记录，不预写。
