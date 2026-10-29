# 一次性私包搬运：独立于冻结790工具

后端AI，2026-10-28，ROLE-backend-TRANSPORT-790-v1。root唯一云操作者；本岗只本地合成验证，不读真实私包。

输入：LOAD新目录生成RSA3072私钥0600，公钥及其SHA经root搬至APP。APP显式指定原S2 control/session/CA三路径和各自公开SHA、实际bindingSHA；可额外指定资源mirror handoff及其SHA。只读取白名单文件，不读取账号/DSN/candidate；镜像handoff归单独mirror目录。

输出：JSON文件集合先base64后gzip，随机64字节拆分AES256-CBC与HMAC-SHA256两密钥，随机16字节IV，RSA-OAEP SHA256/MGF1 SHA256包装64字节。HMAC覆盖版本、公钥指纹、IV、包装密钥、密文的规范JSON。stdout仅PUBLIC hash元数据及每段最多16000字符OPAQUE；若大于18000字符分多段。OPEN须显式pin APP公开PUBLIC记录SHA，核公钥指纹、密文hash及HMAC后才解密，核全部三/四文件SHA、精确名称和control binding/CA，再O_EXCL写新700目录下的600文件。任何失败拒绝输出私密正文且不覆盖旧文件。密钥会短暂出现在本机openssl enc的argv（工具接口限制），不进入UI/日志；同机root为可信边界。

UTC截止固定07:30Z，所有阶段/openssl调用受剩余预算，早到期保留私有/密文前缀，无重试。公钥与PUBLIC记录的来源通过root已认证控制台人工搬运确认；RSA+HMAC保护机密/完整性，本身不证明APP身份。公钥私钥不跨LOAD，依赖宿主原openssl+Python3.10标准库，不新增监听、服务、pip依赖。

先做合成往返、篡改MAC拒绝、wrong public hash、错输入hash、输出存在、权限与分段测试；本地openssl为LibreSSL，宿主Ubuntu OpenSSL兼容尚待root执行。790产品/七文件/manifest不改；不构成性能或正式验收。
