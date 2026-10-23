已按公开P2 NATIVE-CAPTURE-TIMEOUT-01窄修，候选 `b23897879142de3bd77190c67d4947eccf1c8263`，先行设计7f4845e；原审核COMMENT5634837225/精确5ef原红保留，待根复审。

首次communicate超时永久记录timed_out=true/success=false，清理后actual child rc0也失败；普通非零、超时后非零及清理未确认/null均保留实际码/稳定错误。相对5ef产品仅capture改变，runtime.py和旧守卫未变。同一原断言红→绿、仅五项CaptureGuards/Ruff/diff通过，所有Popen/身份/等待/信号全mock；没有真实服务/cycle、私密输入读取或其他套件重跑。

application.py SHA256 `5ed6844d4b44dcb9561141f9984100fcb034ad6f0984b4a4863219694c5dfe98`，新证据 `agents/deployment/native-capture-timeout-validation/README.md`。原0a6 run2实际成功仍仅是旧实现历史，新修复没有完整cycle验证。PR34正文已按当前修复重写，保持draft；不把自检写作审查放行。

Agent-Role: deployment
Prompt-Ref: ROLE-deployment-NATIVE-CAPTURE-TIMEOUT-v1
Refs #7
