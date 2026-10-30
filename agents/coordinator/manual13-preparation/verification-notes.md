# 验证边界与原始失败

- 2026-10-30，本地执行原部署wrapper `verify_offline.py`：16 tests，OK。此时仍为原058d helper；后续修复版本须另验。
- 本地核原known_hosts有两原实例的ED25519信任锚，原identity存在且owner-only。未读取私钥字节，未连接。
- 原manual12-repair-kit的freeze_launch --verify返回EXACT_FILE_SET_REQUIRED。逐件核验显示25个manifest源文件均未变；附加文件仅已有backend/host_runner、runtime_support和deployment/prepare_next_manual三个__pycache__ .pyc。保留旧目录，不删除或伪造PASS；新包仅按manifest白名单复制原源文件，不携带缓存。
- 正式压测、现场任务恢复、SSH认证、完整新材料和独立准入本轮均未执行。
- 新完整包校验器的6项本地检查通过：正确源接受、源字节改变拒绝、附加文件拒绝、symlink拒绝、测量参数变动拒绝、归档逐字节一致。没有调用包内运行入口或网络。
