岗位 backend；Prompt-Ref: ROLE-backend-CAPACITY-V11-IMPLEMENT-v1。

精确8f6e75d的product39956073530/66523真实失败：JUnit391项、2失败、0error/skip，static/frontend成功；两个合法UTC候选返回500。根与backend核对发现服务错误把外层VERSION1.1.0用作内层schema_version，后者冻结const仍明确1.0.0。候选主请求结构在1.1未变，这两个版本具有不同范围。

本次最小修正从冻结ContractValidationResult.schema_version.const读取内层版本，Meta仍1.1.0，14冻结文件/APIREADME/DDL不变。根曾建议候选1.1.1 metadata补丁，backend指出const语义后根采纳最小代码修法；1.1.1未改盘/未提交，AI协商不算用户识别或亲改。新增3category真实HTTP先3×500失败，修后连同原7个UTC正负边界共10通过；原断言未降，Ruff通过。随后对新源精确全CI，不把10项当全量通过。

原CI日志/JUnit保留ignored0600原件，公开副本仅脱敏临时CI会话/DSN密码并附原/副本SHA，见agents/backend/capacity-v11-ci-failure-provenance.json；开发before/after日志/XML也保留。性能暂不运行，第二窗口仅bootstrap成功后服务45秒自停导致sanity ConnectError，0有效样本，是诊断生命周期错误；记录profile-window2-lifecycle-failure.json。
