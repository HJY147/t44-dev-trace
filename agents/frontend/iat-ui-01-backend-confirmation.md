岗位 frontend；Prompt-Ref: ROLE-frontend-INDEPENDENT-UI-FIX-v1；Refs: #2。

前次所问新dev版本与NotificationPage样例已补齐：root明确18080固定02ecdea9ced90cd46cbca898f123d6409f45ba80，backend字节等价3b6dab5，runtime1.0.0/t44_dev。前端实际经5173同源代理访问该服务。

同一经理/项目10，新通知5：GET计数1/1（request_id bca17f1d-99d7-48b7-9901-76b4d51eaa8f），仅handling后仍未读、GET为1/0（8d8450b2-b4b1-4684-94bd-6c2417cf872e），显式read后GET为0/0（c7630a44-b2e3-4fa8-9b11-24db39687e65）。三次task21均state1/version2；未用当前分页items估算，未将处理等同阅读。

fixture由真UI创建task21/限定服务API生成event179、root真实messaging故障fallback产生，不SQL造通知、不重置旧项。原始公共HTTP与计数/截图agents/frontend/iat-ui-counts-browser/counts-result.json。开发回归不是独立复测或Rabbit成功链。
