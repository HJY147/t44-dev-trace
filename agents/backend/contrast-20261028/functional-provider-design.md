# 全新F环境中性五身份provider：协议前核心

后端AI，2026-10-28，ROLE-backend-FUNCTIONAL-PROVIDER-790-v1。只读公开契约/原CLI/原认证源码，不读792私包、未公开用例或真实env/账号；本岗不操作云。源a12；只在新F `/root/t44-r9/campaign-r28p7-01/f`、binding192ff29972aef079ad914139f50bcabbfa5c967ad1c8f2253252ecc226efd59d、DBt44c_r28p7gen01_f、4worker、TLS19443/CAe2a07c50...dc92使用，root等P16停后才起，不触旧namespace。

## 原认证语义

`Settings`只允许TTL60..86400；原Runtime.execute(login)调用prepare验证、原LoginLimiter、identity.login密码校验、issue_session正常INSERT新会话、Business响应契约验证和原audit。只在一个data-only admin进程建Settings(session_ttl_seconds=60)的临时Runtime签新的短会话，不修改F主服务3600配置，不改时钟/已有auth_sessions字段。此正常认证API写入与手工改expires_at/插入伪token有本质区别；后者禁止。短会话以实际数据库created/expires证实精确60秒，自然时间到后原Runtime getMe拒绝，再核已有会话字段未变。撤销专用会话以原CLI `revoke-session --session-id`执行，禁止user范围误伤其他有效会话。

## I/O及分层

数据层核心接收真实factory、原Settings3600、原CLI私密stdin执行器、新账号前缀、显式expired/revocable subject标签和原stop。先核全部18业务表空；五个不同有效用户m/d/d2/r/x只通过原init-user，口令随机且不打印；标签不赋予项目角色，初始不seed业务/不创建项目/任务。五个有效会话均原login3600；额外短60/待撤销3600两会话供后续协议明确用途。只读按原token_digest定位真实session-id，不返回假造ID、不写auth存储。所有原CLI stdout私有捕获，仅解析无秘密的user_id/撤销数量；登录数据只内存/600私包。

协议尚未明确，核心只提供函数，拒绝命令行直接执行；不猜私包键名、不建可被误用的云脚本、不向root打印密码/token。最终字段、recipient RSA、公钥pin、provider nonce、密封格式、撤销时机和私送出口须测试岗通过root提供公开中性协议后再接；不与独立测试岗直接通信。现仅本地合成账号真实SQLite/CLI/Runtime与自然60秒验证。PUBLIC source/archive/image/network/schema/MQ/currentroles等需F实际起后由host只读证明，当前不生成冒充真实环境的receipt；核心只记录实际操作方法/身份ID/时间/数量，不输出凭据。

## 准入和退出

云运行必须核全新F actual binding、53源/归档/镜像、schema/audit、data-only网络、MySQL当前DB、MQ及实际全部roles、F主TTL3600和明确截止；本阶段不编写未验证host壳。任何失败保留部分状态、不重seed/重建账号，stop前每个CLI/事务签发检查，等待不越stop。原始790七文件/manifest、产品零改；独立功能结论不由开发自测替代。
