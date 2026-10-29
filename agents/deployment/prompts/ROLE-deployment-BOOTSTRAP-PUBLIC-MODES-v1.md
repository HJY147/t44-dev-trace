# ROLE-deployment-BOOTSTRAP-PUBLIC-MODES-v1

## 实际派工原文（root转发的云事实，不冒本岗独立观察）

实际云端新结果请做独立role记录和bootstrap根因修补（不动C产品业务、不给独立852私有材料）：original ubuntu24-bootstrap source阶段umask077导致git tracked目录0700文件0600，COPY进镜像rootowned使UID10001读不到t44.cli，迁移15:53:55<1s exit1 /usr/local/bin/python No module named t44.cli。原image backend2c59d266.../webebbc444...保留:pre-mode-repair；源码按C git ls-files100644→644/100755→755及所属目录755（不遍历.git/.env，根目录750），gitdiffclean/.env600，3919files312dirs。API重建15:59:23/110s0，新image2f651f9d76189f500d3d8b7336077c12639d711ac88fc0773b1f88309db9116e；web旧两nginx配置root600，UID101UNREADABLE，重建16:02:34/82s0，新image3255b48594e1763b703ccd5a74b205e9d203c6a1cd89ce6b069e3019327b68bd，实际UID非root配置可读。Ccli sha da883...核验通过，迁移16:03:00/4s0。请在你的branch修bootstrap只保证publictracked canonicalmodes并guardprivate.env不变，报告真实AI审核漏查、失败→诊断→修复，不归学生发现。设计先行/测试新文件prefix846（根只用了847848851），commit/push并Issue留痕既有授权。不要云操作。

## 设计与实现对应

先提交bootstrap-mode-design.md（e9c9115），再846临时Git clone+umask077旧source无规范逻辑反例红，随后只在bootstrap source加入60秒内嵌Python；不改全局umask，不walk、不动产品业务、不在云端补跑。按index规范公开模式并排除私有/symlink/hardlink，.env仅元数据前后guard；其他untracked/.git不递归。修后7用例绿及独立Ruff/语法；原失败、镜像前缀/完整新ID、迁移实际耗时均单列root转述。部署AI实现与前轮AI审核遗漏真实记录，不创造学生发现/修改经历，不读取852。
