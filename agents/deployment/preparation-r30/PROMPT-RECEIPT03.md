# ROLE-deployment-R30-NEUTRAL-RECEIPT-03-v1

实际root派工原文（经root中转，不与QA/审核联系）：

> 加急跨岗P1 R30-NEUTRAL-RECEIPT-03（前一kind修复已由独立审核准确通过并root集成）：QA公开ADAPTER_0B_V24.py SHA694fc3 validate要求原receipt.package_resolution非空dict/list，但准确2ca7 import_backend当前写固定STRING（r30-window.py:110），新adapter必拒，后端不能改原件绕。请最小修复：import_backend已拿到backend()真实observed，把这个真实结构原样放package_resolution（建议同时保留全部60 files/UID/origin/python/sys_executable/business_env_absent，使原import receipt本身就包含完整raw proof，省另一次探针；只有实际backend验证后才写，计数由真实len得）。维持source/bundle/config/identity原证据，不能伪造成dict套旧字符串或放宽QA类型。kind接口v1仍按已发布expected-shape语义；旧未执行候选/历史保留。加本地provider真实函数fake seam→原始receipt序列化→公开QA adapter纯validate 的跨接口正负回归，先保留红，再绿，不执行Docker/HTTP/cloud/SUT/private/core。source/artifact不重建，新adapter/profile GEN/resource hash链相应更新，准确SHA和新pin复审后root才用。今天服务器收尾优先，不新功能。原root预算9e/type remains，预算其他逻辑不改。

实际仅修改provider三行；新增本岗tmp759结构契约回归，不读取任何QA PRIVATE/case/core。公开adapter固定694fc3完整hash后只调用纯validate。输入是本岗从其公开schema构造的SYNTHETIC角色字符串、400条元数据、临时CA解析fixture；没有登录、HTTP、业务请求或实际会话。provider的Docker/backend是明确seam，JSON/save和公开validate是真实函数。
