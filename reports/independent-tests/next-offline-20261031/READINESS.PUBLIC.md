# 下一轮独立离线准入：BLOCKED

候选 exact13acb43a804e717e7485091895378511fe3d9b76。owner worktree为本文件所在worktree，独立新实例，仅经总协调交接。没有云/SSH/SUT请求、没有Docker运行、没有负载、没有当前环境身份批准或一次grant。原p13 NP及所有旧结论保留。

已核v1.2冻结15项及兼容输入1项SHA全部吻合。已定位公开接口 `.agent-worktrees/.runtime/manual13-ready-20261030/qa/READY_INTERFACE.PUBLIC.md`；三个公开Python包装AST可解析。它们固定旧p12身份，既非新轮批准，也不能照旧执行。总协调澄清公开根为主树tmp/753_manual12_independent/PUBLIC后，已读取DELIVERY_MANIFEST.PUBLIC.json并核6个公开包装SHA全部吻合；该manifest仍只列公开包装，不含工具根。当前qa子目录不含冻结tool-manifest或测量源码，已经总协调索取精确白名单，未扫描任何旧PRIVATE。

## 冻结准备方案 v1（不是实现或准入）

只允许未来工具层更正：attempted/accepted/written计数分离；footer记录真正写出认证流的count/plain/compressed；拒绝计数独立；首个停止原因以一次性、可靠、脱敏元数据保存阶段/时刻/尺寸/预留/磁盘free及计数；明确生产者终止、队列排空、writer终止和封尾顺序。任何计数/完整性差异仍fail closed，不得用修footer掩盖未留原始记录。首因元数据自身不可可靠落盘必须阻止完整证据声明。

最小离线工具单元集合：正常记录精确复算；停止后拒绝不增加accepted/written；关闭排空；并发生产者与关闭；各容量分支首因只保留一次；writer异常；磁盘不足/元数据落盘失败；认证截断/篡改/footer不一致拒绝；边界恰等于/超过预算。使用本地合成日志与磁盘查询替身，不调用SUT，不伪造当前环境，不执行400客户端。取得白名单源码后独立形成补丁、检查原全部业务断言保持不变并冻结新工具SHA/用例SHA/离线结果；本方案当前尚未实施，不能宣称工具READY。

## 不变的测量与证据门禁

400客户端、60秒预热、600秒稳态，query/transition/contract/escalation四类P95各≤270ms，每个完成分钟≥1000、零错误、全部原业务/审计/400客户端后置断言，消息实际送达另需原中性证据。原数据规模约40项目/6000任务/9000依赖/15000评审决策，400client/800互异task与真实资格均须核实；不得改指标纳入时刻、桶口径、业务组成、重放/拒绝口径或缩短时长求通过。

## 资源预算（规划值，不是现场核实）

旧公开LOAD预算8CPU/8GiB/2048pids可作为新轮保守起点，不能由旧采样推断本轮足够；APP/DB配置及CPU、内存、排他需当前中性事实。延续旧10GiB plain /11GiB compressed /12GiB cipher总上限作为待校验初值，未批准改大或减小门禁。若三类落盘并存，峰值基础之和为33GiB；需额外计整个工作区/历史run、封存输入、备份双份、临时文件和安全余量，磁盘准入不能只报初始free。单响应、单记录、400在途预留、writer队列和后置预算必须由原工具常量精确计算，当前缺源码故未给伪精确值。旧已有2.50GB明文/0.390GB压缩样本是已观察规模，不能作新轮上界。须覆盖后置及封存时段持续观测free/reserved、CPU/RAM/pids/队列，而非只覆盖稳态。

## 新nonce/material/grant要求

新run、新material、新不可预测nonce及不存在的输出路径；旧p13 grant/material已经消费不可复用。新私密会话/CA/source/bundle/import原件与所有SHA需中性密封交付，仅新独立岗读取。绑定exact候选、工具manifest/runtime/adapter/entry、规格与固定用例、当前APP七角色config、隔离schema/fixture/库存、TLS、LOAD资源/排他、时间窗、所有input SHA及nonce。使用原协议对应fresh default-false和environment精确字节SHA；prepare仅零SUT，环境真实性不能由本地合成check代替。

正式一次grant须后续真实中性审核、用户开跑授权和新工具冻结完成；绑定fresh default-false，只有allow一处变化；真实四session最小expiry减900秒是严格触发上界，身份/会话/schema/输入/资源/排他变化即失效，消费或产生run输出不自动重试。当前未构造或签发任何allow=true文件。

## 必需后续中性材料

1. 原冻结public/tool-manifest.json（预期SHA 78a0aca6e90b61695338a332f7adb1becb5f7eebd13d0c8bd28d3f6ff4f09a05）及工具文件精确白名单根；禁止附旧结果、日志、key、token或内部讨论。
2. 由该manifest允许定位的runtime、adapter、ENTRY、prepare、backup、verify以及固定用例定义；先核hash再按本方案实施工具更正、独立本地验证并另冻结版本。
3. 开机后的当前中性身份/资源/库存/数据与原始记录存储预算/真实零请求prepare证据。服务器现已关闭，本轮不去获取这些实时项。

原始任务书docx/提交注意docx/作业要求txt路径已由总协调给出；本轮尚未独立抽取原件，不宣称已完成原任务逐条映射。候选业务、性能、MQ投递、当前环境、修正工具完整性与资源可用性全部未验证。公开报告只说明离线事实；不能将本文件当开跑许可。

## 后续离线进展（取代上述缺工具路径阻塞）

经总协调允许仅文件名元数据定位，已找到主树tmp/753_fresh_acceptance_90b/PUBLIC/MANUAL_TOOL_V4/tool-manifest.json，SHA=78a0...吻合。仅按manifest读5个非密钥工具文件，全部hash吻合；没有读backup.key或旧结果。将其复制到本owner的private-next-tools。原固定functional、OpenAPI、backup、verify保持原字节；runtime只替换Sink及为原响应完整性失败增加元数据参数，其余逐字比较吻合。新runtime和11项本地合成日志单元已冻结于TOOL_CANDIDATE_FREEZE.PUBLIC.json；11/11通过。没有SUT/网络/云测量。

新工具候选将已接受计数移到队列接纳之后、footer采用writer实际消费计数，保存首因分支/时钟/磁盘/预留/计数并同步落盘，关闭后拒绝新生产者并排空先前记录；writer异常使流不完整并阻止接受。单响应原完整性检查和所有业务门槛原样保留。该候选尚非端到端READY：还缺更新adapter/ENTRY/prepare绑定、完整原始流独立验收器与更全面异常边界测试；本轮不宣称这些已通过。

工具精确预算现已可读：单响应1MiB、单记录/单在途预留3MiB、400预留共1200MiB，队列原上限800记录，FRAME256KiB；reserve磁盘余量门槛128MiB+实时reserved+3MiB，初始门槛256MiB+400×3MiB=1456MiB。工具在线压缩加密，不落明文/压缩中间文件；33GiB仅三种全量另行保留时的保守和，不是本工具实际三份同时落盘。12GiB raw密文之外，整个W备份还可能含历史run，峰值必须按W实际大小/备份压缩上界/复制份数另算，不能只依据旧1.03GB备份。

## 组件离线补充 v5.1

已自行定位并核原公开ADAPTER及ENTRY预期SHA。新adapter仅CORE改绑新runtime，ENTRY保持原字节；未执行ENTRY、prepare或execute。新增独立流核验器检查认证逐帧、唯一终端footer、gzip结束/尾部、多余数据、JSON行及单记录上限、plain/compressed/cipher上限、实际/accepted/attempted/rejected计数，prefix不准作完整记录。扩充至19项合成本地单元，全部通过；含停止后拒绝、关闭排空、并发close、首因唯一、记录/plain/reserve/disk边界、元数据写失败、队列停滞、writer IO、压缩/密文上限、篡改/截断、缺footer及伪造计数。准确冻结SHA见TOOL_COMPONENTS_V51.PUBLIC.json；前v5冻结保留不覆盖。

原任务三件已只读抽取并留SHA：任务书 d772bde097e77082f433c5bbb1bca5ab154fbb0316a5555c211cb532488b0177；提交注意 c688f2a25c8a1c73803e7e958e8c50681a0484ef1f34a679fa8b100ce2d64f32；要求txt 2193bf6c1cc49f3404ae37332759f785e6362c0eb7e3a5e720724a0be0487c3a。400并发、270ms、1000次/分钟及数据规模原约束存在；本轮不声称完成所有非性能交付项验收。

仍BLOCKED：组件单元通过不等于完整工具准入。特别是需要加强并证明全体producer生命周期先终止再footer的协议，防止close/footer之后迟到生产者的拒绝计数未进入终端流；当前合成并发用例只核已接受记录完整，不能当全体生产者时序证明。还需完整release/prepare hash链及合成零请求prepare往返核对。本轮不将这些未完成项移交用户执行，也不签环境准入。

## 最终本轮离线交付 v5.2（以此节及RELEASE_V52为当前状态）

离线准备/组件自检完成，现场准入仍BLOCKED；不是正式工具批准或当前环境许可。已消除v5.1的producer门禁及prepare往返两项阻塞：Sink绑定原400 worker线程列表，close时任何producer仍存活即强制NP，footer显式记producers_stopped，独立完整流验收强制要求true；活producer/已终止producer各有本地单元。新adapter仅CORE更新；原ENTRY字节不改。合成prepare往返只产生临时default-false，CA解析为明确替身；重复run、篡改runtime均拒绝。最终21项logger/raw单元及1项prepare测试通过，全部Python AST、ENTRY shell语法通过；未执行Docker或任何ENTRY模式。新精确工具SHA与绝对根见RELEASE_V52.PUBLIC.json；所有旧冻结记录保留。

正式交付时必须使用新独立workspace及此release的工具精确字节，新public identity必须绑定新adapter/runtime hash；不得运行旧p12 PREPARE_REUSE或旧manifest，不能在原W覆盖安装。原packet中的ORIGINAL_CORE仅是原运输协议provenance，adapter该常量保持原值，不等于grant允许旧测量runtime。未来备份需要独立新backup key；本轮不读、不复用旧key，未生成现场密钥/当前批准。新run/material/不可预测nonce需生成并绑定同一新物料链，原p13已消费物料不可复用。

预算不变：LOAD8CPU/8GiB/2048pids，800队列×3MiB理论记录队列上界2400MiB（不含Python对象、400在途响应、序列化、线程栈与其他工作集）。400×512KiB配置线程栈为200MiB，400在途预留1200MiB是容量记账而非实际分配。原MAX_RESPONSE约束正文1MiB，不应把它误作所有wire/header内存的绝对上界；单记录3MiB越界继续NP，不放宽。实际Linux/镜像/cgroup、长时CPU/RAM/disk水位仍需下一轮中性现场证据，不能由本机小型单元担保8GiB一定足够。备份磁盘预算须测W实际总大小，含旧历史再加新12GiB上限，在线密文与备份、下载副本/临时文件峰值分别核算，不能用固定33GiB或旧采样认定满足。

未验证项：Linux实际运行、真实零请求prepare、真实身份/会话/CA/配置/隔离schema/库存/排他、实际磁盘及整W封存预算、工具发布独立批准，以及全部业务/正式性能/MQ/后置。任何新正式run仍必须另有用户授权与当前独立审核；本轮没有allow=true或一次许可。

## 可搬运安装交付

新包及精确PUBLIC安装入口已完成，见records/qa/next-install-v52.PUBLIC/INSTALL_README.PUBLIC.md及DELIVERY_MANIFEST.PUBLIC.json。新backup key只留独立岗本地及新密文内；用旧LOAD公开收件公钥密封，未读取旧私钥。密文74721字节，SHA f4ac699408a3c00d8cd547cde90be547279c009dda4a94360f8fb0ef3e5d7939。8项安装离线测试通过，仍未执行现场INSTALL/Docker/云/SSH/SUT，未签任何allow=true。新workspace不得复用/覆盖旧W。
