Agent-Role: database
Prompt-Ref: ROLE-database-REVIEW-FIX-v1
Refs: #4 #13

针对审核C-P4，已同步7ce7171并编写迁移checker语义比较源码：索引按有序列/unique/排序及前缀属性比对，并核对index与unique两反射视图冲突；外键比较有序源列、schema/目标表/目标列与动作；CHECK按冻结语法规范化大小写、反引号、MySQL utf8mb4字符串前缀和冗余括号，同时保留布尔优先级/字面量/函数参数。CHECK/FK/unique集合差异拒绝；额外普通非unique索引允许（含MySQL自动FK支持索引）。冻结DDL/API未改。

唯一新测试源码为tmp/backend/persistence/956_schema_semantics.py，包含Inspector替身回归和显式t44_review空业务库受控DDL改动/恢复探针。未读取或修改审核957、独立私有用例。t44_review虽已由root新建授权，但本岗未迁移或测试它。

当前明确状态：未运行、待性能窗后验证。总协调安排正式400并发性能及后续两个600秒批次，本岗按要求仅编辑/源码审查/Git记录，尚未执行pytest、真实MySQL验证或构建；源格式化不是验证。此次draft checkpoint不能视为C-P4已过、全套通过或代码规模达标。窗口后需实际验证正确结构接受/同名错误拒绝、重复迁移行为，再按结果修复。seed公共row-builder减重复尚未实施。
