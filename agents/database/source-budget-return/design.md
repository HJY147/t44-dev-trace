# 代码规模可行性静态审计：先行设计

数据库AI，ROLE-database-SOURCE-BUDGET-RETURN-v1；基root f986782311f227082b4445bf7508522aa49c043d，新codex/database-source-budget-return独立树。只写本目录及本岗日志/module/handoff/prompt；不改产品、DDL/契约/freeze、DB/服务/用例/CI。设计先commit后计数与审查；5分钟内先发数值，12分钟内封档。

沿用docs/metrics/source-counting.md：固定cloc2.10 SHA bf59272455172108072a0a106379f7509fd4349bdcfd85203bac038ccd286d83，非空非注释已提交物理行；应用根仅backend/t44、frontend/src和frontend/index.html，原后缀规则不变。只从指定Git对象归档这些生产源至项目ignored临时目录并cloc --by-file；不归档/读取独立测试、H/H2/private材料。输出原始逐文件计数和按真实生产根汇总，精确对照C6307与3b9c907和本岗AST/scan-run预算。

候选须指明重复片段/调用者、可保守相减的旧行/新增helper/适配器/守卫成本，未实现估算与现有已省分开；用静态源码/已有公开candidate预算，不执行任何测试、profile/数据库/HTTP或负载，不造patch投入生产。只审可信等价抽象，不压行、不挪到未计量配置/脚本、不删业务、权限/并发/审计/错误优先或类型边界；没有1207方案就明说。

先核当前精确总量与各根/重点文件，再用有限重点函数静态读核找重复；来源不足者净节省计0。已做的减重不能重复扣减，互相重叠候选不得相加。Issue4实际公开COMMENT与精确comments/:id GET全文逐字读回；本轮仅静态研究，不以候选行数宣称已达标。
