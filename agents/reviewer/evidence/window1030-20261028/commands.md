# 实际静态核对

源码统一 `git show a8c1f7a2`/`5a88d11a`，部署限定 `git show 4de69da8`。owner明确提供的四侧件只读v3目录，读取时完整SHA在static-first.json。

1. 指定现有解释器以 `PYTHONDONTWRITEBYTECODE=1` 执行 `tmp/791_reviewer_resume_20261028/window1030_static.py`：首次exit0，stderr空，stdout原件static-first.json。只运行Git/AST/raw/JSON/XML/gzip/摘要检查，未调用被审工具入口、产品、网络、云或测试负载。未读解释器相邻env/log/DB。
2. 同解释器短脚本逐项应用已读测试allowlist，与Git原/新文件逐字核同；assert数28/21/17不变；transport交付payload解压同新源码。exit0，结果test-allowlist-transport-readback.json。
3. 读installer-verification六场景及owner XML：只核记录/计数，不执行安装或33/13/6测试。三工具安装指令实际完整base64+256为18836/18648/21668，绝不记<18000。root后续明确18000为保守预算、当前实际经立即不保存通道成功，回传按真实来源保存。
4. 部署profile/generation/resource三SHA同；prepare计划新run_id/output/root02与10:30一致；仅静态时间/namespace审查，无云资源操作。

技术限定准入先交root。后续原件/范围澄清不变更源码判断，也未重投任何指令/读取key；远端提交回执见publication.json。
