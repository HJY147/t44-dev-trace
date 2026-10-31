# 本轮真实诊断压测结论

用户已被明确通知两台均可停机，后续只有本地认证和分析，不再追加SUT请求、重试或新压测。源bcec，原400客户端/60秒预热/600秒稳态。独立报告见records/qa/directp16-result-20261031.PUBLIC/RESULT.PUBLIC.md。性能指标PASS，后置缺项及16错误保留，整体NP；不是原全门禁正式验收。

第一次r3编码绑定失败发生在dockerexec/session签发前；修canonical UTF8（dfef9a82）后用新独占init-utf8工具与正确pin续接，原失败记录不覆盖，未重复任何已开始的负载。实际400barrier UTC09:29:29.584271，FINISHED UTC09:41:09.695740；备份bytes/SHA已核并由独立岗完成AEAD/19文件全hash及149868raw记录认证。私钥、会话、输入明文、原始PRIVATE不提交。

全部稳态请求有完整diag，独立观测18个请求workerPID不等于实际仅18worker；旧只读sampler仅识别supervisor，不能把其worker0误作真实进程0。worker CPU分布未确认。原早晚PUBLIC计数均保原字节；任何窗口均值不替代P95、累计并行SQL时间不当作HTTP占比。
