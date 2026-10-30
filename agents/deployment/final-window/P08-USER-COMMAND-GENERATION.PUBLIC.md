# P08完整用户命令交付（本地生成，不代执行）

所有云动作均由用户亲自执行；下列`python3`生成器命令在root本地运行，只写新的粘贴文件。动态输入缺失、原SHA不符、超期或未批准时拒绝生成；不能把本地校对通过写成云端演练或性能达标。

可选单条方式：`P08-USER-DUAL-PREPARE.INLINE.PUBLIC.sh`（14930B）可由用户在云助手同时选择原两机执行一次，仅按真实私网IP245/244精确路由，其他/混合IP拒绝；两条事实脚本保持原字节。与分别执行两条的方式二选一，不为统一界面重复APP派生。它不启动实例、freeze或发压。

1. 用户亲自开原两机前，root先核实际余额、原实例及平台侧定时经济停机/保盘保护。用户分别粘贴APP的`P08-USER-APP-PREPARE-v2.INLINE.PUBLIC.sh`（8185B）和LOAD的`P08-USER-LOAD-FACTS.INLINE.PUBLIC.sh`（6777B）。两者均离线自包含，不依赖新GitHub下载。LOAD只读取公开元数据和PUBLIC工具SHA，以`network none`原镜像做限制探针，不执行QA、不读PRIVATE/密钥；它可重复生成新的事实回执，不改旧回执时间。

2. root保存用户原PUBLIC输出，自动校对：

```sh
python3 P08-FACTS-CHECK.PUBLIC.py --app ACTUAL_APP_OUTPUT.json --load ACTUAL_LOAD_OUTPUT.json
```

APP v2新增实际私网IP，旧8100B脚本输出缺此字段会被校对拒绝。校对核真实boot/UTC/NTP、双机固定私网IP、source346/90b manifests、镜像身份、8CPU/8GiB/PID2048/nofile4096与无活动QA；freshLOAD超过120秒时显示不能准入，用户须重取，不能retime。

3. root只根据本次现场事实填写新费用原件和`P08-PLATFORM-PROOF.TEMPLATE.PUBLIC.json`，复核后才分别置批准字段。新费用cap50、计价起点取本次实际恢复观察，不复用昨晚起点；原历史boot仅审计。平台证明只要求已真实创建并核对的定时配置：原两实例ID、OOS execution ID、已启用、StopCharging/force=false、相同停机截止和已核单价；不要求虚构一次live停机测试。root_verified仅指配置证据审阅。模板记录root报告的exec-5dd521c335ce4a88a2e7、2026-10-30T03:00:00Z；尚未触发、未观察最终停机、UI通用Stop权限警告均明确保留，不冒称权限完全验证。不是guest关机说明。生成用户APP首次freeze粘贴文件：

```sh
python3 P08-USER-COMMANDS.PUBLIC.py freeze --app-facts APP.json --load-facts LOAD.json --fee NEW_FEE.json --platform-proof VERIFIED_PLATFORM.json --root-reviewed-facts --output NEW_APP_FREEZE.sh
```

用户执行该文件才会异步开始准备；生成器本身不启动。它包含费用/就绪原字节，LOAD观察时间保持原值，APP仍会实查≤120秒与35分钟外余量。S10/E23/G25/C30、400/60/600/780及原门禁保持。

4. 与新phase无关的QA工具资料提前核完。参考`P08-QA-PUBLIC-PINS.TEMPLATE.PUBLIC.json`，九件完整PUBLIC（含F入口与DELIVERY清单）逐个与新LOAD事实和独立QA公开发布件核对，不能默认模板路径/校验和在远端存在；初始`root_reviewed=false`。LOAD第一条只校公开transport-key密文SHA，不解密、不读明文私钥；后续获准的原INSTALL/790才会使用既有LOAD密钥路径，密钥不出机。用户给回新APP bootstrap、原import receipt，独立QA提供新target及其批准原件后，root生成用户LOAD准备文件：

```sh
python3 P08-USER-COMMANDS.PUBLIC.py load-prepare --load-facts LOAD.json --bootstrap ORIGINAL_BOOTSTRAP.json --qa-target NEW_TARGET.json --qa-approval INDEPENDENT_APPROVAL.json --backend-import-receipt ORIGINAL_IMPORT.json --qa-public-pins REVIEWED_PINS.json --root-reviewed-facts --output NEW_LOAD_PREPARE.sh
```

该命令只生成本地文件。用户执行后新建独立`QA753P08`，仅复制精确PUBLIC原件，调用原INSTALL、原790解密/五件提取和原ENTRY prepare；不发SUT请求，不创建allow-true grant。已有workspace/transfer拒绝重放，失败前缀保留。源90b的两份manifest、原service同字节root副本修正均保留。

5. 用户发回`PREPARED_DEFAULT_FALSE`公开结果，现同时附原adapter实际创建的`runs/r30finalp08/grant.default-false.json`完整21字段原字节base64和SHA（中性元数据，无令牌）；root/独立QA审定另给完整allow-true grant，生成用户唯一arm文件：

```sh
python3 P08-USER-COMMANDS.PUBLIC.py load-arm --load-facts LOAD.json --grant INDEPENDENT_ALLOW_TRUE_GRANT.json --prepare-receipt USER_PREPARE_OUTPUT.json --root-reviewed-facts --output NEW_LOAD_ARM.sh
```

arm生成器必须核原defaultfalse SHA/完整21字段及固定工具参数，批准grant只能与该原件逐字段相同、仅allow false→true；截断、额外字段或任何其他改值均在本地提前拒绝。用户须在S−30前执行，生成脚本再次在LOAD核原defaultfalse文件SHA和同一精确差分，再核时钟/入口/grant SHA，单次systemd定时S+1调用原ENTRY。执行器只接受S+1≤真实now<S+20；迟到拒绝、无重试、无继任轮。不把尚未发生的动作写成成功。

**已执行的本地检查**：运行`python3 tmp/753_deployment_final_window/test_p08_user_handoff_local.py`（在仓库根目录），日志见`P08-local-user-boundaries.PUBLIC.log`。使用明确标记的合成事实，验证120/120.001秒新鲜度、NTP/IP/镜像/内存/活动QA负例、过期费用起点和未核平台保护拒绝、QA未批准/PRIVATE工具路径/allow-false拒绝、S−29.999不能arm、S+0.999/1/19.999/20边界（exec spy）。三类生成粘贴均核Python3.10语法且≤16KiB。没有执行任何生成的云命令、Docker探针、HTTP或QA；完整两机流程仍未远端演练。

平台配置更新：根据root现场报告，任务生效中，T44TimedStopRole只对原两实例授权，14:00北京时间之后操作权限DateLess失效；这不是本岗云端复核或成功触发证据。用户预计09:45开机、S约09:55/E约10:08只是计划，实际T0必须由新freeze产生，03:00Z平台截止不能倒填进旧窗口。

原INSTALL调用链已核：直接读取transport-key密文、capsule_tool.py、tools.753capsule、tool-manifest.json；不直接读取外部F ENTRY或DELIVERY。九件是独立QA完整公开交付要求，不能把缺F ENTRY描述成已证实安装失败；本流程只复制校SHA，不运行F。PUBLIC原件清单来源与本地逐字节核验见P08-QA-REQUIRED-PUBLIC.PUBLIC.json。

兼容CLI：原load-prepare/load-arm参数不变。旧prepare输出若没有新增默认grant字段，无须重跑prepare；由用户仅导出指定中性默认grant原件及SHA后，root可在原load-arm命令追加`--default-false-grant ORIGINAL_PUBLIC_COPY.json --default-false-grant-sha256 RAW_SHA`。不得填造默认值或读取其他PRIVATE文件。原adapter、ENTRY、SPLUS1及两条已审事实粘贴脚本完全未改。
