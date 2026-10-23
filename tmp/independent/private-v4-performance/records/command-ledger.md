# 实际命令与失败记录（设计期）

这些是本实例实际工具调用及命令摘要；完整脚本写入内容即本次冻结文件，未伪称本表逐字复刻所有长heredoc。命令均在明确根或独立worktree执行，未执行应用、网络、数据库或负载。控制CLI字符串仅作为将来脚本定义而写入，尚未调用。

1. `git rev-parse --show-toplevel`（原根）：返回/Users/yang/Desktop/nothing/软件开发大作业，exit0。
2. `git show db12bfd4dab03e0b2614f354d8bd27a0e3616621:records/acceptance/v4-performance-neutral-inputs.json`；`cat AGENTS.md`：exit0，只接受明确中性输入。
3. `git worktree add --no-checkout -b codex/independent-harness-v4-performance /Users/yang/Desktop/nothing/independent-v4-performance db12bfd4dab03e0b2614f354d8bd27a0e3616621`：exit0。
4. `git sparse-checkout set --no-cone ...`：只用绝对仓库anchored positive路径；`git checkout`：exit0，未物化产品目录。实际sparse patterns另存records/sparse-patterns.txt。
5. 初次新worktree `cat specs/sources/T44-taskbook.txt specs/sources/homework-requirements.txt specs/sources/submission-notes.txt ...`：exit1。真实stderr：

```
cat: specs/sources/T44-taskbook.txt: No such file or directory
cat: specs/sources/homework-requirements.txt: No such file or directory
cat: specs/sources/submission-notes.txt: No such file or directory
```

6. 原根 `cat specs/sources/T44-taskbook.txt specs/sources/homework-requirements.txt specs/sources/submission-notes.txt`：exit0。随后只对这三指定路径和中性冻结文件计算SHA256，全部与packet匹配；没有扫描别的资料。
7. cat/sed/rg读取specs/requirements.md、business-rules.md、backend-design.md、contracts/README.md、database/schema.sql、persistence-contract.md、field-dictionary.md、changes/capacity-lifecycle-v1.1.md、records/spec-freezes/v1.1.json：exit0。某些大输出在工具中截断，随后只对中性目标schema与DDL段落定点补读；未以截断当完整执行证据。
8. 自写Python JSON解析specs/contracts/openapi.json，提取操作名/请求response引用与相关Schema。只读取契约JSON；不import应用、不实例化SUT。
9. `git show 70f4b7f4ee251830008c1c1a527f1ca05df1db66:deployment/acceptance/README.md`；`git ls-tree --name-only ... deployment/acceptance/`；同commit run.py/control.py中性编排相关rg/sed：exit0。未读取应用源码。
10. `mkdir -p ...`和自写Python校验中性源hash、复制冻结OpenAPI至private inputs：exit0。输出“Authorized neutral hashes verified; no SUT bound.”。
11. shell quoted heredoc与自写Python创建/修订仅私密脚本、用例、decoder和本阶段记录；未import/执行harness_common.py或868/867/866入口。
12. 父协调授权后 `git show db7df7c1b7028f77c10046054d23d0bb7cf8de92:specs/changes/runtime-usage-snapshot-rfc.md`：exit0；纳入其hash和中性副本。
13. `openssl version`：真实LibreSSL3.3.6。`openssl req -x509 -newkey rsa:3072 -sha256 -days 30 -nodes -subj '/CN=T44 independent v4 performance evidence recipient/' -keyout .tester-local/tester-private-key.pem -out tmp/independent/private-v4-performance/recipient.pem`：exit0，stderr仅ignored私密key-generation.log。`chmod 600 .tester-local/tester-private-key.pem`；`git check-ignore .tester-local/tester-private-key.pem`返回该路径。
14. `openssl x509 -in tmp/independent/private-v4-performance/recipient.pem -noout -dates -fingerprint -sha256`：exit0，证书2026-10-23 23:38:01 UTC至2026-11-22 23:38:01 UTC，fingerprint 5D4A8E7551C7486C09E7E6C14284EBB5A1A4474FC8A7A80912E683A2B4505541。
15. `python3 tmp/independent/private-v4-performance/offline_check.py`已真实运行四次；各次工具摘要均 `{"design_static_check_passed":true,"application_or_sut_executed":false,"failures":0}`。最终详情在records/offline-check.json，未将它计为性能结果。冻结前还会再运行最终静态检查，并保存确认记录。
16. `clock curr_time`实际观察点：2026-10-23 23:25:50 UTC、23:32:59 UTC、23:38:11 UTC。这些是时钟读取，非SUT请求。

尚未执行的下一阶段命令：任何HTTP/SQL/Docker/浏览器/负载、workflow dispatch/push触发、加密结果取回/解密。Git冻结提交命令完成后另记commit H的真实输出；只发表metadata。

17. 冻结前只从自有脚本AST抽取Evidence类做两条离线格式/统计向量检查，未import/实例化Driver或应用，未HTTP/SQL/Docker/浏览器/负载。真实通过，验证nearest-rank包含失败、微秒向上取整、吞吐排除失败和gzip原始frame长度；隔离样本只在ignored .tester-local/，不是性能数据。记录records/offline-evidence-vector-check.json。
