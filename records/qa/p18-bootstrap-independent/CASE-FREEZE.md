# P18 初始化独立检查冻结

冻结于接触被测实现前；依据任务要求及冻结产品业务/契约，测试范围仅离线。

1. 400 transition / 400 escalation / 800唯一资源和账户、中文binding、TLS参数保持。
2. 400 transition全量前置检查完成后才允许任何任务写；缺失、project/owner错、其他状态、state3/from非2均拒绝。
3. state2任务零任务写；合法state3/from2以action3及当前CAS、evidence/basis恢复state2。
4. 每次任务写后权威GET；DIRECT采用最新state/version；拒绝结果、歧义写不盲重试；失败无DIRECT。
5. 依赖、权限、CAS仍经产品真实本地API执行，未改业务规则、未SQL修状态。
6. CLI兼容；独占output/newrun r30posttools18，失败和重复运行不改旧证据。
7. 自编离线合成正负例，另检查真实本地API路径；区分真实产品API路由与MySQL现场未验。

不读取作者测试、日志、报告、提示词及期望结果。不发起外部网络请求。
