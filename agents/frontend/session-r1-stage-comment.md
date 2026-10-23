Agent-Role: frontend / AI
Prompt-Ref: ROLE-frontend-SESSION-R1-v1
Refs: #25

收到PR26在精确3c160c5的NOT_PASSED/SESSION-R1审查，原39绿未覆盖“旧错误→卸载表单→旧父刷新”组合。先修订设计7dfefd2，后产品9560e7bd23b68eddbdb733a5ee671999f46a44cd：API在失败处理前后也核对token；OperationForm/WorkspaceView每个回调及await边界核对存活与token；Login旧catch不清新token，TaskDrawer卸载后不继续第二段读取。当前403/409权威刷新、失败logout保留身份、幂等/业务规则均保留。旧401按客户端SESSION_CHANGED取消，当前401仍为真实401清理；未改冻结接口。

公开895原样SHA f42aef302d520ef91ffb9afe3938adba5d2220476f5059e43bb4bd36f00aa2e4，无路径/期待修改，本岗原363重放1红2绿→新源3绿，orphanReads=[]且新身份项目保持。另9个相邻探针初次6行为红/3漏等ElementPlus挂载驱动错误；保留错误，仅增加既有settle等待，在隔离精确3c未改应用源重放3个真实回调红，再当前9绿。原始895/原红/原39绿都不覆盖。一次提前全套48绿3驱动错也如实保留。

最终完整前端51/51，19源行347/373=93.02%、分支755/868=86.98%，main/router仍在分母；构建含类型通过，826.30kB大chunk提示保留。因Login代码有改，原896限定真实1440/390登录、退出200、back/reload、仅当前session真实撤销后UI刷新401；8图已看、60浏览器响应54个200/6个预期401，另2个driver session logout200，0业务写/页面异常/横溢出。浏览器不冒充迟到403证明，后者由原895/组件夹具覆盖。Chrome及自身5176已停止，独立进程和数据未访问。

完整源hash、14冻结hash、原始gzip、旧源/新探针身份及范围见agents/frontend/session-r1-validation.json。此为开发修正证据，申请新的准确HEAD复审；原NOT_PASSED及独立FAIL按原SHA保留。没有APPROVE、reviewer/stage成功、main合并或整产品通过；正式性能、源码规模与学生本人材料门禁不由此解除。
