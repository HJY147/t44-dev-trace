Agent-Role: backend / AI
Prompt-Ref: agents/backend/PLAN-REASON-EVIDENCE-dispatch.md
Refs: #28 #3

HISTORY-EVIDENCE-01/P2窄修源码已push bcb0e1bbb1440df958a04e87afea0e5b015d2f17；设计勘误先提交ad6a9b3f63b1bd810df1e71cfef39cb2cc134baf。AI专审员review_backend_preflight识别并以真实SQLite HTTP确认，后端AI复现/修正，不能记学生亲改或独立验收。原42243审查不通过与原504 CI绿色并列，绿色不能推翻历史候选反例。

原history._matches只用Python容器==，会把合法audit.kind=1与schedule JSON.kind=true视相同而投影reason。匹配输入是旧历史read数据，正常新写原冻结Schema不允许此异常。本岗在原986用真实SQLiteJSON列/RowsGateway/TestClient复制场景，无matcher/gateway mock；旧source新增6案2红4绿（bool与1.0历史字形红），修后6案+1原正常legacy相邻回归7通过、0failure/error/skip。原日志/XML保留agents/backend/plan-reason-evidence-type；18/504/浏览器/负载未重跑，不把这些旧结果移植成新源通过。

窄代码仅history.py：双方先复用冻结EvidenceRefs校验，再按键排序的JSON精确比较。布尔与数值不同，字符串原文/空格不正规化，数组序保留，对象键序不影响匹配；1和1.0虽然均可满足JSON Schema integer，历史候选仍保守按不同字形处理，正常新请求normalization完全未改。非法/不一致候选保留原audit且不猜理由，两行GET前后原值类型/内容不变。另覆盖合法精确、对象键换序、原文改变、数组换序。

只history.py及原986追加，原断言前缀不变；14冻结、DB/runtime/写事务/幂等/outbox/配置/依赖均未改。严格Ruff/format/Bandit通过。单生产文件固定cloc净+4（本Issue后端相对6205累计+99），规模仍未过，不靠压行。新生产文件总数仍44，旧43覆盖分母不可沿用。

设计与派工原文已随先行ad6提交，产品checkpoint随后交给root，本次执行原件另作后续独立证据seal；完整新源组合CI、专审和独立复验由root安排，尚未宣称通过。此前FE872精确0549/旧源浏览器证据继续保留原版本，本修无前端更动不要求为凑新结果重跑浏览器。没有MySQL/私密独立资料/外部负载或服务动作。
