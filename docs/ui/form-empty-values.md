# FE-INIT-01：文本初始值显示 true

## 已复现

米咖阶段实际 5176→18080 的新建任务表单截图 `agents/frontend/warm-glass-browser/live-stable/1440-form-error.png` 和 `390-form-error.png` 中，标题、说明及延期预案在未输入时显示 `true`。本地校验拒绝提交，本阶段没有业务写入。发现者为前端 AI 浏览器视检，不计学生发现或独立验收缺陷。

## 冻结规格与最小设计

TaskCreate.title/description 与 Plan.delay_contingency 在已冻结契约中是 string。`contract.initial()` 对 string/未定 schema 返回 `''`，真正 boolean 返回 false、number/integer 返回 null、明确 const 保持原值；不需要修改契约或猜业务默认值。

代码检查显示 FieldEditor 通过泛型 `defineProps` 声明递归 Json 联合类型。该联合的 boolean 在 string 之前；Vue 编译出的 modelValue 运行时 props 若把 Boolean 放在 String 之前，会把空字符串转为布尔 true。因此需要区分“初始化函数输出”与“组件 props 接收后的值”，用现有测试同时验证，避免只测试 initial() 而漏掉真实控件。

本阶段先在现有 `tmp/frontend/982_client.test.ts` 检查初始化的文本/布尔/未定 schema，现有 `983_application.test.ts` 覆盖 FieldEditor 空文本、真正布尔开关及 OperationForm 真实 TaskCreate 初值。预期控件中的文本为空，checkbox 的布尔 true/false 保留；未知 schema 不推测 true。

若回归证实上述转换，最小修正是显式声明 modelValue 的运行时 prop 接收任意 Json、保留 TypeScript PropType，避免 Vue 自动 Boolean casting；其余 schema/name/path/errors 默认保持原样。不得改 initial()/schema 业务含义、API、校验、状态或独立用例。

## 验证范围

保留改前测试失败，再执行同一组改后；必要 typecheck/build、受影响新建任务表单真实浏览器验证。米咖840b1a8与其原证据不覆盖。未涉及的全业务测试、状态流转与正式性能不重复。若回归不支持根因，记录结果再调整设计，不预先改产品。
