# v3 10:30窗口安装与临界路径

只root云操作。新manifest `0ef08aab3e14887b703c9a2fa5e5265d60fbbcb4172d1d6deb20b5f746df048a`；原source a12、anchor04:00/seed44，截止2026-10-28T10:30Z。工具源5a88d11a；完整安装命令a8c1f7a2。

1. APP与LOAD分别按顺序执行 `split-v3-window1030-install-1.txt`、`-2.txt`、`-3.txt` 的完整内容；完整命令最大16057字节，含encoded与包装<18000，不用再手拼JSON。共同写新 `/root/t44-r9/resume-20261028-01/tools790-v3-window1030-01`；part1独占创建，2/3核同一bundle标记，part3核7件完整hash。每次只输出公开metadata。失败不覆盖或混旧目录；确需新安装目录时3片统一更换新路径，先审改路径，不改内包源/hash。
2. 两宿主各执行 `transport-v3-window1030-install.txt`，完整6374字节，新 `/root/t44-r9/resume-20261028-01/transport790-v3-window1030-01/790_transfer.py`。SHA `7e2dfb5b4c4fd3766769d4c5f15ac65fa8b61e7286e09ee402ff10fa650816f3`。旧07:30 helper不可混用。LOAD先用此新helper `keygen --output-dir ACTUAL_NEW_KEY_DIR`，root将PUBLIC公钥/hash搬APP并预写好公钥新文件；私钥只LOAD，O_EXCL/600。
3. root新profile实际prepare/arm/infra/migrate的r28p16gen02 P phase后，带实际phase/binding/CA/source53/image/no-scheduler六角色事实，先新bootstrap和S1。下列ACTUAL只能来自实际回执，不猜或沿用旧绑定：

```sh
python3 -B /root/t44-r9/resume-20261028-01/tools790-v3-window1030-01/790_bootstrap.py --phase-dir ACTUAL_NEW_P_PHASE --binding-sha256 ACTUAL_NEW_BINDING_SHA --output-name fixture790-v3-01 --anchor-at 2026-10-28T04:00:00Z
python3 -B /root/t44-r9/resume-20261028-01/tools790-v3-window1030-01/790_host.py stage1 --phase-dir ACTUAL_NEW_P_PHASE --binding-sha256 ACTUAL_NEW_BINDING_SHA --fixture-name fixture790-v3-01 --split-name split790-v3-01 --manifest-sha256 0ef08aab3e14887b703c9a2fa5e5265d60fbbcb4172d1d6deb20b5f746df048a
```

root核实际S1候选/selection SHA/完整441对与原P7可比；旧P7公开selection为4bf3514bf8feba68ca81b8e0baa7a13de85fcef095510f9d2f7c8d7e66ee5706。新10:30筛选输入改变，开发只读样本选对未变，不能替代云SHA确认。不碰F，不启动scheduler后仍称正式7role。

4. **确认所有安装、key、公钥搬运、LOAD Python image/hostname证明、运输输出目的文件及逐段提取命令都准备好，才运行S2**。原host命令stage1改edge，其余相同。S2成功后立即从其PUBLIC completion取control/packet SHA，用新版transport seal三件（可选资源mirror第四件独立目录）；显式用新实际bindingSHA/CAsha与公钥pin。APP stdout重定向新public-output.jsonl，不一次打印所有OPAQUE，先只打印PUBLIC、逐段每条任务≤16000 data。真实control/session正文不能进UI/聊天，不能改created_at/TTL。
5. LOAD拼完整PUBLIC+OPAQUE，新helper open并pin APP PUBLIC record SHA，输出新独占目录/600三件inputs。原LOAD命令使用新tools路径与manifest SHA、实际control/packet hash、actual hostname及已证明Python alias/id；先baseline80、warmup800，再measure8000。既有600秒检查、330秒全矩阵准入、每cohort90秒、任何错误共享abort/停臂原样；过期或不全不发下一请求，不重试/续包/放宽门禁。

只完成上述实际root执行后才存在新云结果。所有旧失败/未提交/过期记录保持；本包不自动延长云实例计划或造成费用。未来F必须另新真实namespace/binding/PUBLIC schema/key工具版本。
