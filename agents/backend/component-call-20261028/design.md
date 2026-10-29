# 后端组件Call实现边界

基线5d5e0a15e3b15e2f509c4ae71a927bbc35579be7；独立codex/backend-component-call-20261028。只改backend/t44/services/application.py与common.py两个产品文件，先保存本边界和必要782测试，再执行新目标改前结果，后实施。

Business.dispatch在原collections分支之后、普通getattr之前选择受信静态六operation→owner/method映射；owner缺失仍先DEPENDENCY_UNAVAILABLE，存在时只调用owner(g,Call)，传入同一对象，不自行鉴权/复制/转换字段或开事务。普通集合、其他业务方法、Runtime与FrozenAPI/DDL均保持。

Call.cas的record_diff为keyword-only、默认True。原check_version→构造values/version/time→条件g.update→VERSION_CONFLICT完全不变；仅原before/after两句包在if record_diff内。false保留原列表及其身份，不清空、不新增diff、不影响返回/SQL/审计。仅消息岗未来通知更新可按设计传false；需先保其版本检查在values(row)求值之前。该开关不控制Runtime.audit及持久提交。

必要新边界：六operation准确委托同一g/c；缺组件先于字段读取；cas默认diff/false保留旧diff；false仍保expected覆盖、旧版本/最大版本/SQL CAS失败，不变更diff或输入行。已有SQLite HTTP回归照跑；真实通知签名尚旧的集成缺口必须保留原失败，不加兼容壳或改断言遮盖。无MySQL/云/CI/正式性能/独立验收授权执行。
