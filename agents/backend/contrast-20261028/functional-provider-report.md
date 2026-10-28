# 中性功能材料provider：本地证据与未运行边界

后端AI，2026-10-28。设计c9a03461、核心93bed41d、T12-v2 worker与密封c5870926。只接总协调公开派工，未与独立测试岗互发，未读其private、用例、账号、私钥或日志。仅四个明确授权PUBLIC v1/v2接口各逐SHA核实；v1 Runtime.dispatch标签被本岗按实际源码指出，root转交后独立岗发布v2 Runtime.execute路径；不改独立原件。

当前三文件工具固定尚未启动的旧F：t44c_r28p7gen01_f、binding192ff299...d59d、4worker、19443/CAe2a07c50...dc92、07:30Z hardcap。root07:04通知后续F将另新namespace/08:15窗口，尚未给实际新binding。**此包不准在新F混用或延长旧绑定**，待实际新PUBLIC schema/descriptor后另新目录版本。没有创建任何云F用户/会话或SUT准入，root唯一云操作者。

## 实际本地产物

- 原CLI init-user以随机口令stdin创建五个不同有效用户m/d/d2/r/x，不给项目角色、不seed。全部18应用表初始空；本地正常认证后仅users/auth_sessions/audit_events有预期数据。
- 原Runtime.execute(login)完整请求契约、limiter、identity.login密码、issue_session正常INSERT、Business响应契约、原audit。主Settings3600不变，只临时独立Runtime以replace(settings,session_ttl_seconds=60)签一个新短会话；读整张auth_sessions前后证明只添一行且原行全部不变，并按实际request_id核一条成功login audit。没有手工INSERT/UPDATE/DELETE auth记录、改expires_at或时钟。
- 五主会话3600，短60另session，待撤销3600另session，token与session-id七件互异。云setup worker不调用revoke，六个非过期会话交付前原getMe均200；撤销函数仅后续actual请求按唯一session-id原CLI操作，本地开发测试验证仅它变revoked_at、五主会话仍原样有效。
- 密封使用原锁定cryptography50.0.2（PyMySQL[rsa]依赖），K/IV/token/口令不进argv/env或stdout，内存RSA3072-OAEP SHA256/MGF1 SHA256+AES256CBC/PKCS7+HMAC。T44FENV1精确magic/header/cipher/MAC，canonical ensure_ascii=false、LF、gzip mtime0及大小限制；password从不进入PRIVATE packet。schema严格使用T12-v2 SHA6db48a...e56。
- worker需要root实际F descriptor（来源/归档/镜像/runtime/资源/CA/角色证据hash、source53行、T12新key/nonce、subject标签），其输入本身不是SUT授权。核UID10001/Linux、53实际文件bytes/hash/mode、主TTL/current DB、fresh表、7会话和空业务，写新700目录内600二进制密文和PUBLIC metadata。host-entry/真实MySQL/main未运行，不能把函数测试称整条云worker通过。
- scope只有原PUBLIC线格式编码器：request另一key/nonce、exact有序project_ids、原context不加execution字段、empty iteration_ids合法。真正service签发、scheduler应用和其实际数据核查待准入后actual SERVICE_SCOPE_REQUEST及root原controller成功回执，再做最小私密封装；当前没有预建项目、预发scope或假称'applied_to:scheduler'。

## 执行与证据

三次自然等待独立本地运行分别9、9、最终14目标，**最终唯一14**，不是32累计。最终14=5个公开协议codec/schema/密封/HMAC/keypin/scope-context目标+9个原CLI/Runtime开发目标，零failure/error/skip。实际最终短会话issued06:59:05.847611Z/expires07:00:05.847611Z/observe07:00:06.043161Z，跨60.195550秒；最后测试单独等待51.6785秒，前序真实运行已耗余时。原getMe401 TOKEN_EXPIRED，auth row逐字段未变，五主TTL3600仍有效。该SQLite等待不代表MySQL/云HTTP/独立验收。

证据tmp/790.../functional-provider/packet-core-final.xml与verification-final.json；原两轮XML保留。3文件SHA/字节在helper-manifest.PUBLIC.json；公开gzip投递functional-provider-delivery.json共13168字符，仅工具源码。Ruff最终通过，3.10 AST检查；数据层/密封在原产品Python3.12执行。初查三次旧路径/glob定位失败后按公开真实目录改读，未触private；初lint PERF102/闲置import/FURB162/BLE001先明确兼容及保密注释再通过，未删测试断言。产品/原790七文件/manifest/既有云记录均未改，无新CI、云、费用、业务验收或学生本人经历代写。
