后端935/round8离线诊断（未运行应用或压测）：先设计3e09c86，标准库资源分析工具source1013df013ccd4d2ccb7f687f32d6d46e74a81638，独立分支codex/backend-latency-diagnosis-20261025，产品/主树零改。

只读认证round8.PUBLIC及部署公开metadata，沿interval-interface→final核完整root中性raw：8,301,045B/16,284行/SHA3821564cd1d160cd79f9c66dbdf0facf1907de44e152a750e6a8fee8cc6036f9。steady端点窗每6组600唯一observed/0null；API组平均398.62%=3.986核，generator78.48%，共享MySQL74.03%，不是整机8核吃满或schema独占。原独立mirror尾缺约77秒NOT_PROVEN与formal0保持；不补验收、不归因14个32ms内集中RST，1Hz稳定PID不足亚秒因果证明。

第一具体观测点：935的Server-Timing仅同步handle内至headers构造，漏ASGI/body/线程进入前等待及最后wire/render/send。root可仅从已认证旧raw发布同请求latency/appdur及逐请求残差匿名quantiles（不能两个P95相减）、response_bytes分位；不取源码/payload。后续维护者通用strictTLS快响应400client canary校准HTTP+证据writer，明确非SUT；新独立schema/专用user的source935四路径stage harness接口/观测边界已写harness-interface.json，尚未实现执行，需root另给新环境/准入。

容量仅条件规划：222.79冻结完成/s（含失败）下API组约17.89 CPU-ms/完成，并非请求CPU测量；若400始终在途/无think且目标均值270ms，理想需约26.5 API核，但不是P95数学必要条件或32核保证。当前API未证吃满8核；16可做隔离平台、32在CPU主导后一次对照、64无当前依据。源码7worker潜在105池连接，升16/32worker会到240/480，必须先核DB预算，不能盲升。

旧81c顺序CPU仅历史，list响应热点非本轮四操作，旧也无escalation，不冒935正式根因。不合入旧global ref原型或未测微优化；新产品优化由相应owner和实测阶段决定。报告/输入hash/中性资源统计/源码逐字比较/真实prompt：agents/backend/latency-diagnosis-20261025。无app日志/私件/独立operator联系、无DB活动访问/买云/新agent/重测试，无新cloc；全部作者执行者AI，不冒学生亲历。
