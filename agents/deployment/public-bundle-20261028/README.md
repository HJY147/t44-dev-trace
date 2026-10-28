# 一次下载、两端相同三组PUBLIC安装

固定包commit：`d80ea0578fb436e6f44743aed7d91e10cba3a512`。包`public-deployment-bundle.tar.gz`为120717字节，SHA-256 `8002f6fd51e189382798a3d60d62bf11bbd51891c0b70f92425fd2fc11aed94f`。25成员仅含17个已提交原安装片、7原PUBLIC manifest/profile及新的来源清单；无检查脚本/测试fixture/XML/私包/材料/账号/session/原始云证据。运行代码由原安装片承载，不复刻安装算法。

两端分别直接提交完整 `APP-install.PUBLIC.sh`、`LOAD-install.PUBLIC.sh`；不再base64套一层后仅算内层。APP1925字节、LOAD1926字节，完整outer base64各2568+300描述=2868<18000。APP SHA `ce639cbca02897e136bfeb884438b17aa85e49f980170b12f5ab6b606851c671`；LOAD SHA `0ee9fe57183cf86abbd6f023d0bb3fa5c71c51c066ee943278c3ab3ec601cbec`。精确尺寸/来源/本地检查见wrapper-proof.PUBLIC.json。

每端只有一次curl api.github.com contents API请求：固定上述commit，Accept application/vnd.github.raw+json、API版本2022-11-28，正常TLS且只准HTTPS redirect，不用Token、不访问raw.githubusercontent。原始bytes直接校验；若同一响应是JSON则base64解码，不发第二请求。curl最多60秒、响应1MiB，保存至新私有mktemp目录api.response，不删原响应。随后整个包SHA/长度及所有原件SHA/长度全过，才在内存中顺序bash原17片。

原顺序/目标两端一致，root已确认均未安装：

1. 部署c1303016a053d5b718d3df30ce5911d2e002c18c的6片：新`/root/t44-r9/v4-code-20261028-03/profile`。
2. bridge5f6791308772cab9b53b3eba46acc1d2b1f91831的4片：`/root/t44-r9/scope-bridge-v3-01`，manifest e5512dd264a2199bb599742ea72f671d184ab5e41a3d102bed498d49b244d5f7。
3. P647779681010de99cbb4d5946ded9c4bcd5f8ae132的7原raw片：`/root/t44-r9/p790-f7-2000-ui03`，runtime2af6444892171c1004474379dff699f3ede876c6e7d55e85b72125cbce4626de/delivery305c5a722ee94d1339b2400a292bbc83416e6c40ba3c0a4b7fc49efdcfd41352。不再次封ui双层片。

各原片O_EXCL/内部hash/权限保护原样；某片失败保留现场，不自动覆盖或重复已成功片。旧16Z profile02不碰。安装不调用GEN prepare/arm/infra/migrate/idle、LOAD.prepare/APP.provision/LOAD.deliver、bootstrap、producer、callback或任何服务。只是让两节点具备已审工具。root之后按独立证据/授权执行其实际阶段。

真实本地raw与JSON两路线各执行17个原安装片，只在测试执行边界临时替换三个完整目标为项目tmp793。每次核27份runtime代码+3manifest完整字节及权限；重复首片被原O_EXCL拒绝。整包、内件（含等长SHA改变）、额外member负例均0执行。外层小shell另以实际bash+明确fake curl/captured Python核单请求/响应保存/嵌入core逐字一致；没有把模拟curl网络当真实云连接。原输出gzip及摘要留存。

root当前新prepare计划改选F22443/http18480、P22445/http18481，campaign-f7-2000-01/run r28f720gen01；这只是CLI计划，实际bind_free/prepare回执才准入。此前24443等计划原文和包全部保留，不为端口改GEN/包/重CI；本次安装片也不执行该计划。
