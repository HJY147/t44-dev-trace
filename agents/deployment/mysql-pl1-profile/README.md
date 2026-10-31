# APP64CPU128GiB / PL1 40GiB3800IOPS候选：离线入口

依据DB岗df166675的P13_IO_FINDINGS.md：原100MiB redo、io10000/max20000及写等待突出。该候选不声称P95已修好，不改变全局默认Compose。只调redo2147483648/io1000/max2000；保留flush_at_commit1、sync_binlog1、doublewrite，以及原buffer/instances/page/flush_sync。所有真实执行待开机，由root按既有用户授权核事实，不另问购买/升级权限。

## 默认只plan

```sh
python3 deployment/diagnostics/mysql_pl1_profile.py --expected-seven ACTUAL_ROOT_APPROVED_SEVEN_JSON --output NEW_ABSOLUTE_PRIVATE_PLAN_DIR
```

须APP root，原project=t44-cloud-r30finalp09-p、schema=t44c_r30finalp09_p、原MySQL image b8d06…、7角色root已批准事实；实际Docker ID/image/project/role、原RW named数据卷及卷项目label、datadir/schema、8.4版本/persisted_globals_load均核对。statvfs检查实际卷所在文件系统available bytes >= redo增量+2GiB运行裕量（当前约3.9GiB）；该裕量不代替root另核镜像、备份、binlog增长和全机空间安排，不偷偷清理任何文件。实际物理盘及PL1规格由root控制台/现有证据核准，脚本不把filesystem free bytes冒称云盘级别证明。

原值必须正好100MiB/10000/20000，否则拒绝并交DB复审；不自动对任意服务器调参。plan保存真实owner、effective+persisted值、resize状态、配置快照SHA及旧值。没有DB写入。

## 当前事实批准后apply

approval模板root_approved=false，现场root按真实plan原字节SHA填true、approved_at=当前UTC（5分钟内）、排他已核及资源profile。执行前无其它压测/迁移/写入操作；root确认已有备份和恢复路径，权限可执行SET PERSIST。不是本离线文件已批准。

```sh
python3 deployment/diagnostics/mysql_pl1_profile.py apply --expected-seven ACTUAL_SEVEN_JSON --plan PLAN_DIR/plan.PUBLIC.json --approval CURRENT_APPROVAL_JSON --output NEW_APPLY_RECEIPT_DIR
```

再次核owner/卷/device/expected七角色原字节SHA/当前effective及persisted与plan完全一致，重新核free bytes。依MySQL参数大小约束先SET PERSIST io_capacity=1000，再max=2000，最后redo=2147483648。三条非原子，逐步attempt有记录，失败可能已改变部分runtime与mysqld-auto.cnf；receipt明确PARTIAL_OR_UNKNOWN，不自动后继/重试/rollback。每条mysql CLI凭据只用原容器MYSQL_ROOT_PASSWORD环境内部变量，不打印密码/SQL错误详情。代码不直接编辑mysqld-auto.cnf。

之后读P_S.persisted_variables三值及@@GLOBAL三值必须相等、原KEEP变量保持，等Innodb_redo_log_resize_status=OK且capacity_resized=目标，严格120秒observer界限；动态调整尚在进行/超时即保留partial，不能称成功。120秒仅脚本观察，绝不关VM。SET PERSIST持久于原数据卷mysqld-auto.cnf；persisted_globals_load必须开启，启动参数/配置来源仍须root在重启后重新读回，而非把运行期观测当重启验证。

## 明确恢复，绝不自动缩回

原candidate plan保留旧runtime三值及旧persisted映射。若要恢复，root先评估缩容等待/恢复时间窗、原owner与足够余量，重新生成恢复plan，再以独立当前批准apply：

```sh
python3 deployment/diagnostics/mysql_pl1_profile.py plan --expected-seven ACTUAL_SEVEN_JSON --restore-from ORIGINAL_CANDIDATE_PLAN_JSON --output NEW_RESTORE_PLAN_DIR
python3 deployment/diagnostics/mysql_pl1_profile.py apply --expected-seven ACTUAL_SEVEN_JSON --plan NEW_RESTORE_PLAN_DIR/plan.PUBLIC.json --approval NEW_RESTORE_APPROVAL_JSON --output NEW_RESTORE_RECEIPT_DIR
```

恢复approval.action=restore-pl1-before-values；恢复plan只允许当前三值恰为候选且原owner相同。恢复顺序max20000、io10000、redo100MiB，仍SET PERSIST三条并等resize；无手删redo、无自动重启或缩容重试。恢复的是原有效值并明确持久化，不会把原“某项未persist”的磁盘字节状态恢复成完全相同；原persisted映射保留供root审查，若需RESET PERSIST属于另行受控动作，不在此入口自动执行。

## 验证边界与依据

7纯本地拒绝/正向批准解析、3.10 AST、Ruff通过，无Docker/SQL/云。初Ruff若干import/style/显式check及3.10兼容标注修正后才通过。没有真实SET PERSIST/resize/重启/性能验证。官方：[SET PERSIST](https://dev.mysql.com/doc/refman/8.4/en/set-variable.html)、[redo动态容量](https://dev.mysql.com/doc/refman/8.4/en/innodb-redo-log.html)、[IO capacity](https://dev.mysql.com/doc/refman/8.4/en/innodb-parameters.html#sysvar_innodb_io_capacity)。这些支持动态/持久化机制，不证明本项目性能收益。
