Agent-Role: database
Prompt-Ref: ROLE-database-CAPACITY-V11-CONTRACTS-v1
Refs: #4

本岗基于eac253039cd85873d3b262e648b2b74d94d715a8，只同步specs/database/field-dictionary.md与persistence-contract.md及本岗记录，未改DDL、产品实现、API或旧freeze。依据D005/D006、U015/U016、最终已审RFC bbc4be6/a6271ef7...；这是显式1.1存储语义演进，旧ae60dc3原1.0及11hash保留，当前两文档内容/摘要有意改变，不能再称其逐字等于旧1.0。新freeze父链由root负责，未代其宣称已冻结。

capacity快照跨行校验由服务在同一project锁内重读有效developer和本迭代全量state1–5任务owner集合；6/7可移出，7返工前补回。成员/开发角色保护仍1–5+7，D002转派状态不放宽，无新增预算算法。assignment新增project锁，createTask/changeIteration/rework同序session/idem→project→有序成员→有序task；保留原权限/状态/version等守卫优先，新增人力核对在CAS前。复用422 CAPACITY_REFERENCE_INVALID/审计稳定码30；拒绝不写业务version/plan/diff，成功/旧key重放/独立拒绝审计及提交不明边界不变。

backend已真实直接确认上述锁序、全量owner集合和错误优先级；其API/代码/specs/backend-design/权威与运行副本1.1.0由backend负责。没有把私下消息冒称为其已发表Issue回复。

本岗仅必要静态对照：18表226列及两份DDL原SHA c0e740b203a85117fb125c578ab61401275bbe46ea80c629869c6cff39424bc4保留，226字段/SQL声明不变，旧11hash均可从ae60dc3恢复、v1.json不变，19个本地链接/锚点有效，RFC hash吻合。证据agents/database/capacity-v11-static-check.json。未跑产品/MySQL/迁移/pytest/全套/coverage/独立/性能，本轮不计这些通过；既有live结果/失败不重写。操作者AI，不记学生亲改；未联系独立tester或读取其私有资料。
