# Posttools v1.1：已知缺陷，不可部署

保留旧v1，v1.1仅增加schema强引用寿命保护和版本号。5092真响应+2400变异差分、10000临时schema寿命、13退出码和400/8582完整历史重放通过；正常30.799s，400快照/400审计，全部owner/reader/pool/writer先退出再global close。1秒预算+2秒延迟64在途只清理、不补PASS；503一错保持ERROR。

额外配额延迟边界发现：reserve前门禁后被延迟，reserve返回晚于deadline仍会发HTTP。准确重现见RESERVATION_RACE.PUBLIC.json，故此版本不可批准。原5件冻结源不改，另v1.2修复并补admit/reserve/HTTP dispatch/response/validation/下一页边界。原测量loop/client/call/Metrics字节继承不变，旧Direct16 NP不回写。本地macOS回归无Linux quota，不是云验证。
