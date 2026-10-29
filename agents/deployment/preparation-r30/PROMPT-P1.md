# ROLE-deployment-PREPARATION-R30-BUDGET-KIND-v1

实际root派工原文；本岗仍不接触审核岗或QA私件，所有中转由root负责：

> 限定审核发现且真实离线复现P1 R30-BUDGET-KIND-01，BOOT和SUT grant继续HOLD：准确a605的r30-window.py:160 generation kind 改r30-official-backend-production-entry-window-v1，但携带mysql-budget.py(305f9e) checked_binding:81-82只接受exact-pinned-production-entry-generation-v4，实际checked_binding抛V4_ONLY_NO_OLD_CAMPAIGN_ADOPTION，operation_lock/probe-budget/admit均进不了。20旧本地边界漏此真实接口。root没开云。请修复严格版本兼容链：可仅派生R30预算kind、新pin/hash且保留旧305f原件/其余预算逻辑并拒旧kind，或保原kind另加严格R30source/run新约束；不能放宽到任意kind/删checked_binding/绕预算。先独立复核保留红，再实际端到端derive→binding→预算入口(operation_lock/probe-budget的非网络路径)红绿验证，再给新准确commit/hash复审。无云/全产品CI/新功能，今天收尾优先；不联系审核岗，只root中转。

另一次实际root要求中性manifest/loaded接口及资源枚举：

> 用户刚要求今天尽量结束所有服务器工作，root优先一次35/40/45分钟有限窗口。请直接给新source manifest 0c5b... 与backend bundle manifest b2db... 的原始文件绝对路径（仅manifest无源/凭据），以及loaded/import60新proof的公开中性schema/path/hash接口。QA工具责任岗确认v2.4 core源无f7硬锁不需改，只新PUBLIC adapter需读这两原manifest和loaded证明。通过root转，不联系QA。另请明确newprofile真实APP服务枚举/角色与scheduler状态，避免镜像件数/运行资源数混淆；不扩张新开发，不启云。

实际采用第一条允许方案：预算模块仅一处KIND literal变更，新hash反向pin入generator并继续resource链；旧305f原件和所有预算算法不动。tmp760先红后绿，保留首次红，追加实际跨文件入口检查，不把原20项宣布成兼容性准入。loaded接口只文档现有函数的中性序列化方法，没有发行真实proof。
