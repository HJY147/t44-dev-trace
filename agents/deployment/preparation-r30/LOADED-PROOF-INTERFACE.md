# R30 loaded 中性证明接口（供root转交，不联系QA）

本页是路径/schema/命令约定；当前没有真实APP加载证明文件或其hash。CI文件探针不充当loaded证明。两份官方原始manifest保持原字节：

| 角色 | 原始绝对路径 | SHA256 |
|---|---|---|
| source | `/Users/yang/Desktop/nothing/软件开发大作业/.agent-worktrees/deployment-preparation-r30/tmp/761_deployment_preparation_r30/official-artifact-12880320744/source-manifest.json` | `0c5b0c0e027578b0f62711175beac4680aab8331bfbc4af2547f02398f38cc1b` |
| backend bundle | `/Users/yang/Desktop/nothing/软件开发大作业/.agent-worktrees/deployment-preparation-r30/tmp/761_deployment_preparation_r30/official-artifact-12880320744/backend-bundle-manifest.json` | `b2db2e1c5cf56fa5df4f20f7003d44d6b3b9ab4cd484b45d921c82640295d345` |

QA中性adapter只需这两manifest和未来真实loaded proof，无须读其相邻源/镜像、部署日志或任何凭据。

现有 `r30-window.py import-backend --receipt <new PUBLIC json path>` 成功后才排他写 `r30-backend-import-receipt-v1`。它绑定source/bundle/source-manifest、image identity、full_runtime_files=60和package resolution；**它不含60行实际文件表，不能冒充完整raw proof**。receipt本身SHA由root按实际bytes计算。若QA需要完整60行，用下面现有backend验证函数序列化实际结果，不修改执行器core。

建议新云路径：`/root/t44-r30/<new-run>/loaded-runtime-proof.PUBLIC.json`。这只是未来路径约定，文件目前不存在；由root实际完成import后运行。`R30_PROFILE`为新修复后profile，`R30_PACKAGE`为已核本轮七件artifact目录；所有变量传普通路径，无口令/会话。

```bash
python3 - "$R30_PROFILE" "$R30_PACKAGE" "$R30_HOSTROOT/loaded-runtime-proof.PUBLIC.json" <<'PY'
import importlib.util,json,pathlib,sys
profile,package,output=map(pathlib.Path,sys.argv[1:])
spec=importlib.util.spec_from_file_location('r30_loaded',profile/'r30-window.py')
window=importlib.util.module_from_spec(spec);spec.loader.exec_module(window)
a=window.artifact()
bundle_hash='b2db2e1c5cf56fa5df4f20f7003d44d6b3b9ab4cd484b45d921c82640295d345'
bundle,source,identity,observed=window.backend(package,bundle_hash)
value={'kind':'r30-loaded-runtime-proof-v1','source_sha':a.SOURCE,
 'bundle_manifest_sha256':bundle_hash,
 'source_manifest_sha256':bundle['source_manifest_sha256'],
 'image_alias':bundle['declared']['alias'],'image_identity':identity,
 'runtime':observed,'runtime_file_count':len(observed['files']),
 'runtime_file_set_sha256':a.digest(a.canonical(observed['files'])),
 'backend_file_count':sum(r['path'].startswith('backend/') for r in observed['files']),
 'business_services_started':False,'volumes_modified':False}
a.save(output,value)
print(json.dumps({'path':str(output),'bytes':output.stat().st_size,'sha256':a.sha(output)}))
PY
```

`window.backend`先完整验证artifact与源，然后用原image-proof将实际Docker29 descriptor/Id与归档config/layers/DiffID闭环，再实际执行none/read-only/UID10001文件探针；它检查完整60运行文件、`find_spec('t44').origin=/app/backend/t44/__init__.py`、业务环境缺失。`runtime`只含uid/package_origin/python_version/sys_executable/business_env_absent/files，各files行是path/bytes/sha256/mode。没有账号、令牌或Env值。不会import业务应用或派业务请求。

中性adapter应核root实际公布的整proof SHA和bytes，schema kind/source/两manifest hash，runtime uid=10001/origin/业务环境缺失，实际60 rows与source manifest去掉两Dockerfile后的完整集合相等，backend count=53，file-set canonical hash相等；镜像identity分清actual_id与config_id，不能要求两者字符串相同。任意缺项/错hash拒绝。当前不预填success或proof SHA。

## APP服务角色与scheduler状态

- 每phase配置的PERSISTENT七角色：`mysql,rabbitmq,api,consumer,scheduler,web,tls-gateway`。这是资源枚举，不是镜像件数或实际运行数。
- `infra`只启动mysql/rabbitmq两常驻角色；`idle`再启api/consumer/web/tls-gateway，预期六个常驻，scheduler仍未启动。
- scheduler必须精确项目scope的真实服务token以及显式`scheduler-start`后才是第七个；不可按镜像已存在或配置已生成就记scheduler running。
- operations profile的`migrate,admin,credential-admin`是一次性容器；不计入PERSISTENT常驻数。resource collector/systemd observer是外部观测进程，另列。
- F/P是两个隔离phase，各有七角色枚举；本轮只按root准入phase依次运行，不把未启动phase计入实际资源。最终实际数量/角色/scheduler状态由新status的逐资源state.Running/absent和真实unit/PID证据记录，不预写。
