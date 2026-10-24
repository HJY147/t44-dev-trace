Agent-Role: frontend / AI
Refs: #28

收到后端候选方案：在既有after条目使用field='reason'/value原文；旧记录只在project/task、from-to排期版本、actor/time和完整plan全精确匹配时批量只读投影，缺失/歧义不猜、不改原审计/DDL/schema。前端接受这个来源要求，不从临近时间或另一类理由补写。

补充实际静态核对：通用RecordView会完整递归渲染after[]，dd的pre-wrap/overflow-wrap没有正文截断；但现状{field:'reason',value:'原文'}的field键没有中文label，会显示“补充信息 reason”，reason已有中文label只在对象key时生效。value还会经过通用display的时间/operationLabels转换，不能无条件宣称任意理由原文都已原样显示。

后续另派前端UI003阶段需要：识别该理由差异条目，显示中文“原因与决定依据”，对其value按用户原文纯文本呈现，不作为HTML执行、不把日期开头或操作名理由转换成别的内容；长文与换行按现有详情布局完整显示。旧历史没有可唯一核对的理由时，提示应贴在该条任务计划变更记录旁：“此历史记录未提供可核对的变更理由”，不让缺省空白冒充已经补齐，更不生成替代理由。如何识别缺失仅限后端明确的相关操作/记录范围，需在读取方案中写清，不能给所有审计行加此警告。

这些只是接口及显示需求，已同步后端岗位；当前UI002代码仍仅forms/OperationForm，不改历史、冻结字段或数据。待总协调准入后再实施和测试。
