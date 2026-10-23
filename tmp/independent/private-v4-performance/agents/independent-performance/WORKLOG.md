# 独立性能v4工作日志（尚未发布）

操作者：AI独立测试实例/root/independent_performance_v4。无学生参与记录，不借用开发者、审核者或以往独立结果。职责：本阶段仅中性性能用例设计与H冻结。

## 实际阶段与材料边界

- 从明确工作根读取当前AGENTS和db12bfd4dab03e0b2614f354d8bd27a0e3616621指定中性packet。未读取项目README、他岗agents日志/提示词/报告或任何以往独立轮次资料；未与开发或其他子agent联系。
- 使用git worktree add --no-checkout在/Users/yang/Desktop/nothing/independent-v4-performance新建codex/independent-harness-v4-performance，自有索引。positive non-cone sparse只选择AGENTS、指定中性材料和自有目录/可发布metadata路径。没有使用root索引、没有自行选择SUT。
- 首次在新worktree cat指定三原始txt失败，真实exit1，三个No such file or directory；它们未在中性commit物化。改到明确原工作根读取相同三原始文件，逐一核对packet SHA256全相符。没有改写或提交第三方原材料。失败不隐藏，原始错误原样记录在records/command-ledger.md。
- 读取中性规格、OpenAPI/DDL/持久契约/字段字典、freeze清单与运行README。只为安全编排读取70f4b7f4ee251830008c1c1a527f1ca05df1db66的run.py/control.py相关片段：context字段、超时、私有凭据交付、audit文本格式、允许CLI。没有读取/import Python/TS/Vue应用代码；中性实现不是被测产品源。
- 独立形成三入口、数据计划、采样/统计与失败规则。三个入口均使用完整600秒稳态；不把预热、准备或三个短段混算。所有真实脚本、decoder、离线checker均只在约定私密目录。400定义为闭环虚拟用户，明确866双步骤用户循环而非400个同时在途升级请求。
- 只向/root提出中性资源观察能力需求；读取其随后明确授权db7df7c1b7028f77c10046054d23d0bb7cf8de92的RFC。选择性观察不依赖尚未承诺能力，缺失如实unknown。
- 生成RSA3072接收者和自签证书。私钥只在本机.tester-local/且0600，git check-ignore确认ignored；私钥/凭据不纳入H。默认本机OpenSSL实际为LibreSSL3.3.6，不能据此声称将来CMS解密已验证；此刻仅证书生成/有效期检查，未运行加密传输测试。
- offline_check.py只AST解析/compile自有脚本（不exec编译对象/不import驱动/不import应用），核对输入合同hash/version、数据规模代数、依赖前驱不回滚、局部合成输入Schema、接收证书至少一小时有效。真实摘要passed=true；不是SUT行为或压测结果。脚本编制过程中在冻结前修正自身数据字段/窗口守卫/证据压缩/语义oracle等；没有任何失败的SUT运行可被掩盖。
- 当前实际HTTP/SQL/Docker/浏览器/负载执行次数：0。SUT绑定：无。正式性能结果：NOT_RUN。完整限期2026-10-24 01:43UTC不改变阈值；若无法完成正式运行应如实未运行。

## 产物与保密

cases-and-criteria.md为真实设计；harness_common.py和868/867/866入口为真实将运行脚本；decode_raw.py可导出完整timing。inputs/source-hashes.json保存中性材料出处与hash，inputs/openapi.json为冻结契约副本。records/offline-check.json是最终离线检查原始结果。freeze-manifest.json将在H前列出全部文件sha。只发布metadata路径/哈希/准确H/范围，内部文件、日志、密钥、密文与解密输出未授权root/开发查看。

下一阶段必须等待/root另给准确SUT及运行绑定；本阶段不dispatch、不push触发运行、不借中性环境commit当SUT。H之后任何机械修正使用新H并记录等价边界，绝不降低原阈值/数据/稳态要求。

冻结前补充：只从本实例自有脚本AST抽取Evidence类做2条离线格式/统计向量检查；未import/实例化Driver/应用，未访问SUT，不是负载或性能样本。真实通过，样本仅在本地ignored目录，检查摘要纳入H。
