# ROLE-deployment-UBUNTU-BOOTSTRAP-v1

本岗为本次实际总协调派工建立归档ID；原文如下。

用户现已明确授权为官方Workbench创建角色 AliyunServiceRoleForECSWorkbench/策略AliyunServiceRolePolicyForECSWorkbench 并继续部署；root刚在弹窗点击确定，正在等免密连接结果。请开始下一阶段独立工作树准备一份可审查、短小且有界的Ubuntu24.04主机bootstrap脚本/步骤（不接触云，只供root经官方Workbench执行）：安装必需的官方Docker Engine/Compose或Ubuntu签名仓库Docker+Compose v2及Python3.12/git，克隆公开HJY147/t44-dev-trace并严格检出准确C 0dfb55c2191200d947c5423fd9ee74bb0812cc5a，验证HEAD，不打印任何凭据，不改网络开放/凭据，不启用收费产品。先只准备主机环境、源码、config-check/build/infra/migrate的最短分步命令；不初始化用户口令、seed或正式压测；不要写一键全执行危险脚本。root需先看脚本/命令才可在新云主机运行。可把脚本放本岗责任目录，预算/截止固定北京今天17:00，所有外部下载设超时/失败退出，不用curl|sh，不申请云key/token。实际执行你没有权限，不动共享集成工作树/其他服务/CI/测试资料。尽快回传第一阶段可审查命令，后续写本岗记录报告prompt并commit；建议不重复安装已满足项。
