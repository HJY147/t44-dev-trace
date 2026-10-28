# P64安装分片：修复未计外层base64的审核阻断

后端AI，ROLE-backend-P64-UI-ENCODED-V2，2026-10-28。仅重分片，不改原13 runtime、业务、grant、原46用例或任何运行算法。旧d17cf53c/manifest1da/四脚本和原9检查保持；原“raw+300”只能证明raw大小，不能证明实际base64外层交付合格。这是本岗漏测，不能用后来的GitHub API下载成功追认。

27bcdd3d先在旧件真实运行4个outer-base64+300断言，结果3 failed/1 passed，实际20444/21640/21112/12968；原JUnit无损gzip封存。新builder只调用旧安装函数构造同一runtime内容，分片raw上限12000，另给完整可直接粘贴的UI launcher；此launcher将raw脚本base64解码后交bash，所有包装和300字节说明一起计数。

| 片 | raw字节 | base64(raw)+300 | 完整UI命令+300 |
| --- | ---: | ---: | ---: |
| 1 | 9389 | 12820 | 12942 |
| 2 | 11750 | 15968 | 16090 |
| 3 | 11418 | 15524 | 15646 |
| 4 | 6194 | 8560 | 8682 |
| 5 | 10970 | 14928 | 15050 |
| 6 | 8350 | 11436 | 11558 |
| 7 | 9501 | 12968 | 13090 |

新目录 `tmp/790_backend_contrast_20261028/p64-f7-ui-encoded-v2/`。delivery.PUBLIC.json SHA `243d90ca022aaf1d336854066fd9c65e9e49a65f20047594d22fae95184097c5`；每个raw/UI完整SHA见该文件。runtime manifest仍为 `1da8ff5eaede6d6349c04ee8c3208a85ea2628b6a7604351e9dcfe332feb1de8`，所有13件/两grant模板/原46测试文件按d17逐字相同。

新目的目录 `/root/t44-r9/p790-f7-1600-ui02`，独占新目录，不覆盖旧安装。两种互斥使用方式：root若使用自动base64包装的既有执行helper，应传raw-part01..07.PUBLIC.sh；若直接填购买侧控制台命令内容，则按序原样填ui-part01..07.PUBLIC.txt，这些已含完整base64外层，禁止再包装一次。配置中的tools_dir须指向实际选择的安装路径；grant内容/业务参数不变。只有第7片最终核齐13件和原manifest后才算代码安装完整，不代表SUT准入或压力通过。

本地7检查全部通过：逐片真实完整长度、UI解码与raw逐字相同、实际outer→bash→安装完整回放（仅目的路径重定向至新自有tmp）、umask077、13源字节/模式、首末片拒覆盖、混bundle拒绝、旧runtime/grant/原测试逐字未变。最终JUnit `final-ui7-local.xml`，原失败 `old-encoded-red.xml.gz`。没有重复产品或压力测试，没有云/独立私件/SUT/CI/费用操作。

根告知固定GitHub commit API公开代码下载已成功；本岗没有执行或验证该云路径，也不拿它替代这次完整UI回放。新delivery及commit交审核岗复核，原68本地业务检查不能冒本次交付门禁。此为AI过程错误/修复记录，不是学生本人经历。
