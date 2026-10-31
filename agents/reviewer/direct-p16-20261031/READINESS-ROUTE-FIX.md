# DirectP16 真实405路由顺序修正

准确9d0d5a3d358c687d5b71c059b822d8f0d0c7a4b9（root884635ba）源级审核无阻塞。旧GET-only探针没有覆盖实际bcec POST先注册的Starlette PARTIAL路由，上一离线审核未发现该假设；真实失败应继续保留，不能由旧READY推断可用。

本次只改OPTIONS成功判定为405、非空Allow且方法集合仅POST/GET、JSON对象严格等于标准Method Not Allowed（非任意文本/任意405），不要求业务请求或鉴权绕过。原SQL SELECT1、严格CA/原SNI/8443、响应大小、28秒截止与29/30秒外层限制不改。它证明基础连接及路由响应可用，不表示业务鉴权/队列/测量指标通过。

本岗只读本地准确commit，纯内存3正例（POST/GET/二者）及8负例全部通过；owner MANIFEST每项SHA通过。新增router_checks固定真实bcec API SHA974ede，真实FastAPI两顺序且patch Runtime.execute抛错以禁止业务执行；本岗已审这些测试的断言，没有重跑全产品suite或660秒演练，没有SSH/云/真实Docker/外接服务器/QA PRIVATE。

最终包与ROOT新exclusive路径仍待审核：旧/root/t44-direct-p16及QA753_DIRECT_P16保留失败历史；只有新r3前缀可供后续单次显式执行。当前不授予READY/通知开机。
