# 新functional专用profile事前设计

root在2026-10-28明确另开功能阶段：原诊断P7/P16截止07:30Z不变；新functional源仍a12e9e70b963bacafda3242bb6d82e53ee912ff1，新截止08:15Z，复用原双机。预算/开机事实由root决定及操作，本岗不操作云UI、机器、IAM、费用或原数据。

使用既有已审derive-resume-profile，在本岗全新local目录生成显式新源/新截止的profile及generation/resource；保留旧派生件、绑定和成绩。`r28funcgen01`符合原`[a-z][a-z0-9]{5,15}`（首字母r，总长12），不需换名。新hostroot为`/root/t44-r9/functional-20261028-01`，generation输出`/root/t44-r9/campaign-r28functional-01`，F TLS22443/http18480、P22445/http18481，Pworkers7只prepare不启动；后续只F4worker空库与真实五身份。

沿用原daaf factory、源a12已证明actual镜像和完整同源source package作为只读输入；新generation绑定自己新代码/08:15、全新namespace/DB/CA/端口。新profile builder仍精确相同源/依赖，摘要应与此前ebc91一致；如果不同拒绝，不替换旧builder。源/完整文件数、原四模板SHA、派生builder→generation→resource链先核，再将profile.json/generation.py/resource-stream.py打包为小公共运输；运输只含公开代码/元数据，不含env、身份、nonce、证书私钥或会话。

本地验证仅合法runid/新端口、真实Git完整源/冻结比较、生成代码解析、完整SHA及08:15不回写07:30、运输完整解包且拒覆盖/路径穿越。root唯一执行者，收到实际prepare/arm/config/infra/migrate回执后才能谈功能环境运行；本岗不读792/private，不将计划写成已执行。
