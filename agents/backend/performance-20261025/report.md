# 实际请求线程 CPU 诊断与引用展开原型

后端 AI 编写工具、执行本地诊断并分析。不是学生手测、人工改码或本人手写研究报告。基线 ade5e4c；最后工具源码25b1e10cab76270c20be579d39aa1c3048033266。产品/backend、frontend、部署和冻结合同/DDL对ade5逐字无差，正式源码仍6316/超1216，本阶段没有生产修复或新cloc。

## 实际执行和边界

834_request_profile.py导入不连接/执行，显式--run、准确HEAD和已提交源码校验后才启动。输出限定本岗目录、O_EXCL/O_NOFOLLOW0600固定fd。实际FastAPI TestClient＋生产Runtime/Gateway＋本进程内存SQLite，3个合成用户、1项目、20任务，准备HTTP不计入请求样本。每组4预热、4路径各12计量、4独立cProfile，共56请求；不是400并发、600秒或P95验收。

计时包裹APIRoute的实际同步处理线程，记录request_id/UTC/monotonic/threadCPU。阶段包含关系保留，inclusive不能叠加；exclusive只减直接子跨度。客户端wall分开记，不把它减handler当纯排队。cProfile只对单独4个样本运行，计时器为thread_time；其开销不混入12个计量样本。

首轮16014aa构造的pending block缺evidence得到422，原4条warmup/错误JSON与日志保留。05e4仅修合成输入为有证据的manager block/unblock，后续成功断言不变。初测及原型曾end_wall早于end_cpu，极短span CPU可超wall最多459ns；发现后25b1e10改end_cpu在end_wall前，旧原件保持，再必要重做一对同源基线/原型。最终两组各56均200、各868span均CPU窗口在wall内、exclusive非负。

## 修正时钟后的描述性对照

以下均每路径12个计量样本中位数，单位ms。原型只在tmp替换诊断进程的factory，未进入产品；响应始终由原factory独立校验。

| 路径 | 基线handler CPU | 原型handler CPU | 基线client wall | 原型client wall |
| --- | ---: | ---: | ---: | ---: |
| getTask | 1.439 | 1.458 | 2.294 | 2.313 |
| listTasks（20任务夹具） | 7.796 | 5.865 | 8.942 | 7.089 |
| validateContractPayload | 0.716 | 0.749 | 1.577 | 1.636 |
| transitionTask | 4.139 | 4.091 | 5.207 | 5.006 |

基线listTasks的API schema阶段CPU中位5.825ms，Runtime1.746ms；validator构造仅0.032ms。独占profile成本主要在jsonschema.descend/evolve、referencing.pointer和wire，**不能用inclusive榜单相加当互斥CPU份额**。这支持调查重复引用遍历，不支持把旧构造缓存当主要解法。

仅tmp的局部引用展开原型使用每调用memo，不跨请求缓存，当前SPEC没有ref siblings或scope/dynamic关键词；遇ref siblings、$id/$schema/anchor/dynamic/unevaluated或循环直接回原factory。35个纯开发差分、回退、错误序、SPEC逐调用变动与并行局部状态检查通过，JUnit源c499fc302774ca6d847f149dd7812fdeb6b2d5ec；后来只driver时钟修改，原型和测试字节未变。复用旧870公开合成样本函数作为部分输入，没有运行旧guard/main或移用旧版本指标；不读独立私有用例。

大列表handler CPU约降24.8%，但小GET、校验没有一致改善，流转接近噪声。因此**不直接全局部署这个原型**，也不增加正式源码来声称解决性能。样本顺序、Mac负载及SQLite差异未作隔离控制，不能把其差值称云端因果改善，更不证明270ms或502根因。

## DB与root对接

曾实际装DB岗c11/f102…观察器执行新增一次56请求，真实HTTP成功；该观察器也随后发现微小时钟端点问题，旧件保存，不把它冒作最终edc3/4edbf…模块的新运行。root的fresh MySQL CI应使用最终观察器SHA `4edbf24779794a826bbe754ccad26890ea4c5c1d3f13f05778bad0e52ec307a9`。

驱动MySQL必须CI=true、--allow-mysql-ci、DATABASE_URL/T44_DATABASE均指root新t44_diagnostics、localhost和显式期望库名。root先迁schema；驱动只预检19应用表空后初始化合成数据，不读旧env或私有凭据文件、不执行MySQLDDL。本岗未执行真实MySQL、云、服务端口或网络负载。API工具最终SHA `150c019e1e307475cec6d599c7f85ac402b9c2f263d4020b8ff02590e08bff7e`，Observer path+SHA成对准入；SQL文本/bind/token/正文不存。

## 原件、真实失败和后续

六份JSON原字节无改动地gzip压缩，raw/gzip双SHA、大小及roundtrip在artifact-manifest.json；其中含失败、初测、旧DB仪表、旧原型、最终两组，各自source准确记录。summary.json仅最终对照的派生统计。35项JUnit、日志和verification.json保留；import两工具且禁止t44/sqlalchemy/fastapi/pymysql加载，实际无输出通过。最终三文件Ruff/format通过。

初次Ruff自动修1个import顺序，原型SIM105检查失败后仍先提交5a2、再d540显式改suppress并通过；时钟patch首次上下文不匹配未写入，随后按实际格式修复。未把这些工具失败冒产品缺陷或隐藏。原TestClient弃用warning保持。

下一步先由root fresh MySQL诊断确认SQL/commit/CPU份额与实际配置，再选择局部优化或受控worker对照；正式云复测另由新独立流程冻结。云839的0完整正式组、3个502和所有未完成后置条件保持。没有指称CPU、DB或网络已经是根因，也不向独立岗发送本分析。
