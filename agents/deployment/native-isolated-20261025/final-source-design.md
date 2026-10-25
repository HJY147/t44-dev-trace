# 最终应用绑定扩展（未启动应用）

root后续要求候选真实CI结束并明确最终SHA后才启动应用，故准备时ade5快照/原manifest与已运行guardian保持不变。新增isolated-application.py，只在root给定40位SHA后导出新的application-<SHA>运行子集、逐文件核验并生成独立application-binding.json；旧ade5资料不改标签。新controller以新文件存私有run，不覆盖正在运行的controller.py，原guardian仍按同一state拥有权协议停API/consumer/scheduler。

唯一可读DB输入是root显式给出的continuation-20261025/independent-functional-db/application-env.json，只校新t44_i829_20261025和专用同名appuser、127.0.0.1:13306；不读取admin、identities或登录凭据。新AMQP拼接自本轮broker的0600JSON，不打印连接串。最终源backend锁必须匹配已核依赖；实际inventory/pip check再核。新绑定文件包含native build身份/完整运行子集hash/树OID/执行文件/参数/端口，不声称Docker镜像或全仓checkout。

API仅原生TLS127.0.0.1:18096四worker；启动后严格本轮CA+IP请求既有projects无凭据接口，仅401视为鉴权路径连通，不登录/创建数据。worker仅枚举已匹配自有supervisor的直接子进程，核UID/PGID/PPID/cwd和命令指纹并登记；consumer同源单独进程。scheduler必须等root单独给fresh token路径及明确UTCexpiry，拒绝不够60秒余量的凭据，不猜项目ID或自行签发/续期；本轮锁和60秒源规则不改。启动异常只清本轮已证明拥有的应用进程，broker/guardian保持可审状态；所有原始日志私有。

只增本岗合成门禁：选定新库的URL/用户名/端口拒绝、精确SHA、token窗口、PID指纹/workerparent/cwd；不运行独立用例。实际最终源、API/consumer/scheduler结果须后续独立记，不借broker或旧ade5准备成功宣称应用通过。
