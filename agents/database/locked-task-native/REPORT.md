# 已锁任务行复用候选：本地原生RC正确性验证

产品a59a90a1，开发测试69dff6f4；三个产品文件对git对象逐字比对通过，哈希见SOURCE.PUBLIC.json。原INSERT-first候选9c8369ec拒绝结论保留，未叠加。

自建全新socket-only MySQL 8.4.11，128MiB buffer pool，skip-networking，不连接云、不接触已有PID7980/13306实例。服务器默认RR仅是启动观察；实际SQLAlchemy connection明确READ COMMITTED，SELECT @@transaction_isolation=READ-COMMITTED。运行真实原DDL及seed_demo合成数据；加载候选完整模块，不替换claim或模拟gateway。

candidate2实际通过：12线程各用不同幂等key、同task/version发BLOCK，恰1成功200，11个409 VERSION_CONFLICT；持久化任务version仅+1，state=3；审计1成功+11拒绝。主事务等待其他持有者FOR UPDATE，持有者更新并提交后，候选locked_scope返回最新version及原因。跨gateway上下文拒绝INTERNAL_ERROR，错project上下文拒绝RESOURCE_NOT_FOUND。SQLAlchemy handle_error无驱动错误。自己的服务器shutdown exit0，socket已消失。

原始失败：首次项目.venv缺pymysql，改用已经存在的database-scale-r29-venv，未安装依赖。candidate1合成BLOCK漏evidence，12项均422 EVIDENCE_REQUIRED，断言失败；原JSON/stdout完整保留，补合法证据fixture后以新datadir/socket运行candidate2，未覆盖旧结果。该次失败属于开发验证夹具，不是修改产品绕过规则。

范围：这是数据库岗开发正确性检查，绕过HTTP入口的validate回调以隔离事务层；HTTP输入/输出契约由已有开发测试和CI覆盖，不能将此结果称为独立验收、完整HTTP/CI通过、P95改善或压测达标。无上下文原读取回退的开发负例属于后端既有4项context测试，此脚本未独立重测所有回退组合。旧p13 NP_NOT_ACCEPTED保留。

命令：在本worktree执行 PYTHONPATH=<backend-locked-task-reuse-20261031>/backend <.runtime/database-scale-r29-venv>/bin/python agents/database/locked-task-native/check.py candidate2。标准输出、退出状态和公开JSON在本目录，脚本及SOURCE.PUBLIC.json可复现。操作者/夹具作者为数据库AI，非学生亲自测试或手写研究报告。
