# b5a16e6 Actions 实际核对

实际操作者：AI消息岗；Prompt-Ref: ROLE-messaging-APPLICATION-v1。总协调要求核对既有失败，不修改原始日志、不改其他岗实现或断言。

两run的headSha均为 b5a16e6273eaeff5768aa20c977d42fbecbb9aca，整体结论均failure。静态job成功不等于镜像构建成功。

| run | contracts job/第10步 | coverage job/第10步 | frontend job/第10步 |
| --- | --- | --- | --- |
| [39925904582](https://github.com/HJY147/t44-dev-trace/actions/runs/39925904582) | [120322087652](https://github.com/HJY147/t44-dev-trace/actions/runs/39925904582/job/120322087652)：contract 26pass/1fail；integration 24pass；fault 4pass/1fail | [120322087806](https://github.com/HJY147/t44-dev-trace/actions/runs/39925904582/job/120322087806)：269pass/1fail | [120322087459](https://github.com/HJY147/t44-dev-trace/actions/runs/39925904582/job/120322087459)：ERR_PNPM_NO_SCRIPT，缺test:coverage |
| [39925978579](https://github.com/HJY147/t44-dev-trace/actions/runs/39925978579) | [120322332159](https://github.com/HJY147/t44-dev-trace/actions/runs/39925978579/job/120322332159)：contract 26pass/1fail；integration 24pass；fault 4pass/1fail | [120322332297](https://github.com/HJY147/t44-dev-trace/actions/runs/39925978579/job/120322332297)：269pass/1fail | [120322332448](https://github.com/HJY147/t44-dev-trace/actions/runs/39925978579/job/120322332448)：ERR_PNPM_NO_SCRIPT，缺test:coverage |

两个contracts日志的integration段均显示 `backend/tests/messaging/test_rabbit.py ...`，fault段均显示该文件 `..`；两个coverage全套同样显示该文件 `...`。b5a16e6文件只有三项测试：

1. test_real_confirm_ack_loss_redelivery_and_connection_restart
2. test_real_mandatory_return_fallback_terminal_and_new_event_recovers
3. test_real_poison_message_goes_to_durable_quarantine

该文件使用真实 PikaBroker/真实MySQL，CI无配置会fail而非skip，日志中三项均通过；因此可确认首阶段真实Rabbit这三项已经执行成功。连接重建不称broker服务重启验证，不将这三项推成整条流水线/独立验收通过。后来增加心跳、列表范围锁、DB恢复的当前SHA仍需新CI。

所有Python失败均为 test_missing_notification_dependency_returns_real_503：默认组件已自动导入NotificationFacade，实际200空列表而旧夹具期望503。根已排BE显式故障注入修正，本岗保留原失败、不修改外岗测试。coverage job先有测试失败，不能宣称全产品覆盖率门禁通过。frontend本branch基线尚未纳根的完整FE实现；本岗未改前端或部署。

原始archive API字节未改动：

- 39925904582.zip.bin SHA256 = 24277976aff94253035d2b64ee5722f04e5c7c78ddf54311e551b75b59c08fa7
- 39925978579.zip.bin SHA256 = 245c1d6b13b84313266f5faa36fe1ed43411f82a559577897f2f5cda332bdc69

各关键step和完整job日志gzip是对archive entry原字节直接压缩，未去尾空白、未改换行或修改失败文字。checksums.json记录原archive SHA、gzip SHA与解压后原entry SHA，-metadata.json保存实际run/job/step及SHA。公开CI日志作为证据原样保留；不是独立测试私有资料。
