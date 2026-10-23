Agent-Role: messaging
Prompt-Ref: ROLE-messaging-APPLICATION-v1
Refs: #5

本岗已将真实通知门面与消息进程第一阶段提交并推送：b5a16e6273eaeff5768aa20c977d42fbecbb9aca，draft PR https://github.com/HJY147/t44-dev-trace/pull/20。

产物为 backend/t44/messaging/、backend/tests/messaging/ 及本岗 WORKLOG/模块报告/handoff/prompt与原始运行日志。默认 NotificationFacade 对齐实际 API，限制本人recipient和active membership、通知CAS，read与handled独立且不改task。Pika持久拓扑、persistent+mandatory+confirm、DB提交后ACK、重投/死信隔离、升级fallback终态/普通事件retry已实现，语义为至少一次。

本地24项通过（16基础/SQLite/fake通道/配置、8真MySQL含HTTP与通知并发CAS），3项真Rabbit因本机无服务未运行；消息模块覆盖85%，Ruff通过。真Rabbit测试使用实际连接/mandatory-return/DLQ，不是mock，CI缺AMQP/DB直接fail。

缺口：DB confirmed超时缺失通知恢复门面待接线（Issue4 #issuecomment-6360793043）；原有contracts回归25通过/1失败/1跳过，缺失依赖夹具在默认组件现已实现后需由BE显式注入故障，已报根并保留原失败，不越权改外岗断言。尚未跑真实Rabbit/托管CI/独立验收或性能，draft不宣称完整进程已验证。

首次GitHub issue发布与PR创建曾返回EOF；均先查状态再重试，未把失败计成功。当前由AI消息岗实际操作，不计人工亲改。
