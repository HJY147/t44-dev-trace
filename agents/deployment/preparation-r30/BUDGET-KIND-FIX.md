# P1 R30-BUDGET-KIND-01：严格kind链修复

root转发限定审核发现；本岗独立重现。原a605的generator binding kind变R30，而其携带预算仍只接v4，原20项边界没有实际进入预算接口，漏检成立。BOOT/SUT继续HOLD。

先新增tmp760（核root/worktree均未占用），以真实官方artifact运行derive，写新0700 phase/0600磁盘binding，加载派生budget。首次5项真实运行结果为3 FAIL+2 ERROR；operation_lock和实际GEN operate(probe-budget)路径均抛 `V4_ONLY_NO_OLD_CAMPAIGN_ADOPTION`。原红日志 `budget-kind-red-first.log` 不覆盖。

修复只把预算模板中唯一 `KIND = "exact-pinned-production-entry-generation-v4"` 派生成精确R30 kind，拒绝任意/旧kind；旧305f原文件完整保留。新预算所有其他字节相同（测试直接对全文件作一次literal替换后逐字比较），没有删checked_binding、改锁、预算、观察、measure/admit/receipt或绕过入口。

- 原预算SHA `305f9eaeea96b0ef882ec17a457f51852bafc8c34b5fe2e47056bd12625dd82d`。
- 新派生预算SHA `9e98632fa1885bf4327b04a95daeba5cee4ad909b536e91ac8b11a1e58488a61`。
- 新adapter文件SHA `f2f850b5e17bd688811413ac535d36c0345ec9a0472df18dc22b65e758342896`。
- 新GEN的BUDGET_SHA pin改新hash，GEN实际文件SHA再进入resource链；profile分别列original_budget_sha256和derived_budget_sha256。GEN/resource最终hash依实际窗口而定，不用fixture hash冒充真实窗口。

同5项首次绿色：准确R30 binding被接收；真实fcntl lock进入；实际GEN operate(probe-budget)经新budget binding/锁检查后到达mysql live边界；旧v4 kind拒绝；全预算只改kind且新pin相同。GEN外部phase_binding/systemctl/live使用明确替身，mysql live直接抛非网络哨兵，**没有Docker、SQL、实际Linux timer或SUT**。因此证明kind链入口已通，不称actual-budget采样或admit已云通过。

原7项window窄回归通过，保留原全305f身份断言并新增derived hash断言，没有降低既有要求。首Ruff因新增测试unused json F401失败，原日志 `budget-kind-ruff.log` 保留；删unused import后最终Ruff绿。adapter和派生预算Python3.10语法解析通过，仅语法，不等于3.10实执行。无全产品CI/镜像重建/云动作。

root需复审准确新commit；旧a605 profile另新目录重派生。新中性/PUBLIC调用者若要加载budget，必须接本轮profile新9e...及相应binding，不再pin305f接R30。原source/bundle manifest和准确0b镜像未变。loaded证明当前不存在，其未来PUBLIC序列化接口单独说明，不能填预期成功。
