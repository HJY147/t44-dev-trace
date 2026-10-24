# ROLE-deployment-TLS-DELIVERY-v1

本ID用于本次实际派工归档，不改写用户原话，不计作用户亲自改码。总协调先准入最小TLS设计，再发以下执行任务；部署岗仅在自有worktree实现，云执行仍由root单独审查授权。

## 本次实际派工原文

准入你刚给TLS delivery最小设计，请现在直接完成最小production helper+wrapper+必要检查，单独新branch/worktree从root当前（可读取gitrev或你a0后branch也可，但root冲突可控）。不等build结束再编码，不云执行。sourceC原样，private runtime配置保存app RFC1918 IP，443不公网；gateway8443私网+同nginx原digest+edgeonly，rootCA key不挂，只leaf0600RO，验证SAN，严格TLS；overlay DB/MQ同digestECR。运维wrapper必须对C/clean/0600.env/privateoverlay校验并显式双-f，可白名单config-check/infra/migrate(plan或--execute)/seed/token/start(--no-build)/status，带绝对deadline/适当单阶段timeout，不自动串阶段/回滚/删卷。跨需要fixture admin stdin调用由backend另独立计划，先不包credentials。优先可审核心代码，文档简短。实云v2 policy生成15:00:24exit0hashf910...，FROM-only probe15:02:28/86s/exit0，镜像ID5909...ce6且成功标记；完整C build v2已提交仍待回执，600s/云720，不宣称成功。

## 后续实际进展原文

最新实际完整build v2：15:13:15，601s，exit124 timeout；web镜像已实际build/export/unpack成功（t44-web:local），api仍pip依赖下载（最后可见coverage/cryptography下载）。保留日志，正只读检查buildxhistory/进程，未盲重跑。请继续TLS helper必要检查/提交不要暂停。下一若需PyPI mirror会另明确外置delivery Dockerfile唯一--index-url补丁、原C不改、require-hashes不变，现尚未采用。

## 实施前设计与本次取舍

沿用已准入：产品C不改；单独私有0700目录，精确overlay同摘要ECR+私网TLS旁路；根CA key不出主机，叶key0600只读；同一工具兼作资源生成和单阶段wrapper。每次先C/clean/0600.env及manifest核验，再两份显式-f；操作不自动串联。prepare/pull分别显式，token仅首次签发，不造账号API/不包口令。绝对17:00释放减120秒，整阶段预算含preflight；失败私密保留，不擅自回滚/重试。

必要检查仅本地stdlib合成和本地真实证书生成。macOS LibreSSL3.3.6缺-checkip，原失败保留；生产目标Ubuntu OpenSSL3严格命令不改，guard仅以stdlib解析实际SAN替代此工具缺项，并明确chown mock。没有Docker、云、CI或独立用例动作。新工具仅能力交付，不等于正式压测或产品准入。
