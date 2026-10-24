部署根因修补 ROLE-deployment-BOOTSTRAP-PUBLIC-MODES-v1：先设计提交e9c9115，再实现59b7d2f7f0af1ab8baa836ec3baea859bccb02a7（codex/deployment-bootstrap-modes，基root44e315a7a33d6802651013d911ecfc91731dd2a5）。修订deployment/ubuntu24-bootstrap.sh SHA256 9786139dfb39583f8809fd2c39044ea8ea441f9df55ed22032d8c323190f1929；产品C业务/旧镜像/20元/17:00不动。

真实原因与责任：原全局umask077保护秘密，但Git tracked公开目录0700/文件0600被Docker COPY为root-owned，非root UID10001/101不能读Python包/nginx配置。本岗AI实现及此前AI限定审核漏查此边界，由root AI诊断修复，不归学生发现。原8f脚本/云失败和旧镜像均保留。

云事实仅root实际UI转述、本岗未云验证：迁移15:53:55/<1s/exit1 No module named t44.cli；root按Git模式修3919files/312dirs，tracked clean/.env600，原backend2c59d266…/webebbc444…保留pre-mode-repair。API15:59:23/110s0新image2f651f9d76189f500d3d8b7336077c12639d711ac88fc0773b1f88309db9116e；web原两个nginx配置root600且UID101 UNREADABLE，16:02:34/82s0新image3255b48594e1763b703ccd5a74b205e9d203c6a1cd89ce6b069e3019327b68bd，实际非root可读；Ccli hash da883…据root核验，迁移16:03:00/4s0。迁移/镜像回执不代完整API/TLS/私网/正式性能。

最小预防修补只在bootstrap source阶段加入60s内嵌Python：保留umask077，核精确HEAD/clean，按index stage0 regular100644→0644/100755→0755及其父目录0755、根0750。先整体校验owned regular/非symlink-hardlink，以O_NOFOLLOW+fchmod防误改；不walk .git/.env/其他untracked。已有.env仅lstat要求owned0600且前后元数据不变，不读秘密，不自动修私有权限；最终HEAD/clean再核，失败不自动回滚/重试。

846本地临时Git clone+umask077复现旧cli.py600，原逻辑公开644断言红1（原件保留）；修后7项绿，涵盖模式/exec、env/git/private untracked不变、错HEAD/dirty/不安全env/hardlink/unsupported symlink拒绝。tmp/deployment/846_bootstrap_modes.py、内嵌Python分别CI Ruff0，bash-n/compile/stageddiffcheck0。无云/安装/镜像/服务/新CI或852/其他独立资料动作，未在root已修云目录重跑。详见agents/deployment/bootstrap-mode-validation和更新说明。
