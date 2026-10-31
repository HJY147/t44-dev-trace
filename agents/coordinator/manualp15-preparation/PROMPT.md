# 本轮用户原始要求与执行边界

- 用户：「现在需要开启服务器进行测试吗，你先做好准备，准备好以后告诉我开机然后马上进行压测」
- 用户追加：「下次连接服务器不要临时授权直接永久授权」
- 操作者为AI总协调，不记为学生本人操作或研究报告。仅离线准备完成后通知开机；目前两原实例保持关闭。固定岗位分别负责backend物料、deployment镜像/顺序、独立testing新准入。无硬件对照、无自动关机、无旧grant复用。
- 产品准确源bcec3326b40814fdb1922bbfea7c29473b47ba47，CI off41169683822/on41169697472。新run r30manualp15 / material r30materialresume09 / maintenance r30restoretransition09 / LOAD workspace /root/t44-final-20261031/QA753_NEXT_V53。
- 长期SSH只添加原受控公钥的restrict无expiry条目；继续校验两原hostkey、私钥不搬到公开包。不要求两小时窗口或旧temporary receipt，真实连接仍须开机确认。
- 原400客户端/60秒预热/600秒稳态/四类P95≤270ms/逐分钟≥1000/零错误和全部原断言保持。诊断缺失为unknown，不能丢慢请求或把缺失记0。
