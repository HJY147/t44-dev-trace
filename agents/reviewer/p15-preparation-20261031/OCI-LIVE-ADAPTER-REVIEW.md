# P15 OCI 最小兼容修正审核

结论：9b6bbd87 及本次指定 APP 公开适配器无技术审核阻塞；不代表 fresh material、轮换、完整扫描、独立 grant 或正式压测已通过。产品 bcec、测量工具及全部原业务断言未在该修正中修改。

依据本轮 root 明确授权，仅经既有 SSH 读取指定 PUBLIC 工具、原 import receipt 及其 observation，并远端只读 stat；没有执行 Docker、SQL、HTTP SUT、材料或轮换，没有读取 QA PRIVATE。不同于上一轮离线审核，本次实际使用了授权的只读 SSH。

- backend exact 9b6bbd879a17fcd2c865b104ba519585416a2245：core 只将 classic config-only 改为严格双身份；config 仍是原 bundle/identity config，actual 必须等于明确 auth.expected_api_image_id。不同身份额外要求 identity==identities.backend、OCI kind、三个严格 is True、层数为正 int 且排除 bool。source/bundle 原字节、UTC 非未来、历史链隔离等原检查保留。
- 原 producer image-proof.py 实际实现验证 actual descriptor digest、归档中 descriptor/blob SHA 与 size、原 config、逐层 diff-id/编码、labels/platform/rootfs。审核了实现与公开 receipt；本岗未重新读取镜像归档或重算全部 layers。
- release-oci RELEASE 全10文件 SHA/bytes 独立核对；除 refresh_core.py 外其余9文件逐字等于旧 release，包含 host_runner.py。新 core SHA 2121d3fb2f42ed5b242edfa3fcef17011c19bf58afcd08054e8ea01de75bcfd6。
- APP 原 receipt SHA 92c61bac4a89f08fa0b4624c6dcccda5a9a77b866104c5847126664f38ad7ed3，14327字节；与公开 observation 的实际 uid0/mode0600/mtime_ns/size/SHA 全相同。receipt 与 observation 的 observed_utc 相同；本岗没有读取包含凭据的 auth，因此第三个 auth 引用时间由原 host 守卫执行，不宣称本岗已验实际 auth。
- 原 receipt identity==identities.backend。backend config479c4065→actualf1061d92、web config866ce20b→actualdda00443，均11层，三个 proof 严格 true。原 source52d741/bundle3e09cc 绑定沿用。
- APP snapshot_phase.py 相对 r2 仅 BACKEND/WEB 两常量替换为已证明 actual；原完整 Env、资源、卷、网络及 infra 门禁代码逐字保留。rotate_current.py 仅 IMAGE 替换；maintenance_v3_oci 仅 NEW_CORE_SHA 替换，SHA886fe6d0dbd65802d78a54e81958f7314b3e952c57a5f96b208de6df88763b0f。
- rotate_scheduler_token.py SHA47640ba975f210b9ca7e7f66e718711f42766093bf6a0e3749f0f60ae210fe8f、observe_full_scan.py SHA6b6911876b871df4620c4128bd1c9281926a592be55c6215c7e877223a0a7bd3 均逐字 r2 不变。公开 adapter manifest 的单项 rotation SHA 已核；其他文件通过实际逐字差分与公开 proof SHA 核对，不将该单项 manifest 误称覆盖全部适配器。
- api-web-ready-seven.PUBLIC.json 实际 SHA af34ef232b8d127c09536082c685ab1f33882349b02c3a5d3ffbfc22a8cd720d，source bcec，phase api-web-ready，root_approved=true。本岗仅读取公开审批元数据，未重执行 snapshot 全门禁。

55c12896 PUBLIC 事后封存 wrapper 已静态读：固定原 backup manifest hash、写者停止显式证明、容器退出、14GiB tmpfs、29GiB MemAvailable 下界、树/密文容量限制及28GiB容器上界；不改变测量8GiB。尚非实际封存或下载验证结论。保留原字节证据，无自动 VM 停机动作。

本次不为现有400任务计划修复授予额外验收结论；root 所述正常经理 PATCH 后仍须原完整资格检查、原800 IDs/历史失败前缀保留和新 baseline，据实完成现场门禁。无新增产品测试/全套 CI 请求。
