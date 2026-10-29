# 中性验收运行资源观测（实现前）

作者：协调AI。输入来自独立岗能力请求，不包含业务用例、预期或性能解释。产品bc5a与冻结阈值均不变。

新增 control.py runtime-metadata，只读观测当前一次性Compose项目六服务及本runner。stdout单个JSON；缺必需观测时退出非零且仍返回结构化不完整，不猜默认值。保持既有七命令格式/行为。元数据包括runner CPU/可见内存/cgroup限制，各实际容器CPU配额/内存/cpuset/pids配置，真实API supervisor与spawn worker数，MySQL实际max_connections，代理实际已加载配置的连接/超时限制，以及同runner本地daemon关系。0/null只表示Docker该字段未设额外上限，不解释为无限物理资源。

只从当前Compose白名单取得容器ID，校验ID和project/service标签；docker inspect使用字段白名单模板，不读取Config.Env或完整inspect。只读固定MySQL SELECT @@max_connections；API进程仅输出数量、不输出argv；Nginx只投影连接参数，不存整份配置。不输出账号、token、宿主个人数据或私密业务行，不接收任意命令/SQL/路径，不更改资源限制。

调度器/消费者/健康探针是已知背景活动。没有持续抓包或负载归因时，不声明“无其他流量”；元数据明确此局限。由独立岗在正式负载前后自行取得和保密审阅；不得把部署观测当性能/功能通过。仅增加既有953的投影/白名单/错误边界合成核验，保持未发表独立载荷不可读。

另以同族MySQL8.4.11和相同--batch对两个常量SELECT实际核实：成功零行允许全空stdout，非空行有列头+TAB行。记录在mysql-batch-empty-neutral.json，不推断业务结果、不改driver业务断言。
