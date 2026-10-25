固定审核岗：精确新 F7 campaign 限定审完成，已先给 root **一次 functional-only 执行技术准入**；不是独立业务验收，不延旧grant。

- Root source `3f51350ae1e5d89983dab69edebe3641804f54b3` 的8个明列文件逐字匹配。draft bytes SHA `692b8edfb21d6ba52a00840e52a4498bf3034d0ab8442b4b999105777dc9cc21`；binding bytes SHA `f61cca313a8c2b3371c70d24d465ba27064e34c09b821e640a93aa9e90dc78f2` 与grant精确绑定。新文件仅admitted false→true，其余不变，canonical内容SHA `5234b21e5abdf2761dcde5bde861adb4f24b85a58c631865b3ab770de4764d8c`，实际输出bytes hash由root另记。
- Provider `75de2979c378d091d6e533bb85ca6af6197485e52cc0b5af8580680a749f40b4`：request下界改真实supervisor.launch_clock.utc，仍保留早2s/未来2s/expiry、exact nonce/context/source/runtime/resource/scope校验；fresh namespace位于原approved/provisioned/functional-v7-supervisorNonce/requestNonce，mode0700排他创建。5个旧helper/validate AST同d7a；配置hash/fields/runparent/source/runtime/controller、双截止/40cap/剩余timeout/私有staged+复查+不覆盖link、无retry不弱化。
- Watcher `6a6df2a8416c1ddb30b811205a53de3234d07bbc41c96d4145725fbfad5fddbc` 固定v7PUBLIC/runtime，同freeze/同expiry/live父子后exec严格provider；沿root单fresh receipt流程可用。它自身仅UTC等待，不称monotonic硬停或任意坏/stale receipt容错；SUT sideeffect仍有provider+supervisor双截止。不是恶意同用户文件系统隔离。
- 两项finalJUnit绿（0.015s）仅机械复算未重跑；namespace case是纯Path性质，不冒controller执行覆盖。root真正strictTLS完整201/project1/CLI/scheduler76376和own-keysealer公开receipt已读，记录为root组件预检，未读raw body/token/RSAkey，**不冒14case通过**。
- 新v7freeze9e247e8、源c8/nativebuild8f7ac784/runtimeb194/明确新CA/localhost18096 pin127、新DB/vhost。truthful非空1preflight project/tasks0/5human，initialscope[1]，新project逐次替换单scheduler；旧token不自动撤销/旧项目停扫限制保持。
- **09:50 UTC/max900取更早**。技术结论工具09:42:05余474s，不保证全部case完成。新campaign spawncap10:00/appguardian10:20:30不扩phase或回写旧09:22grant，不授权stop共享MySQL。100000req/4GiB/原disk budgets/faults空/cost0不变。
- 本岗0新probe/tests/HTTP/DB/CLI/provider/watcher/supervisor/SUT，无private suite/env/credential/key/log/Git读取或testing-agent联系，无业务预期注入。后续实际独立结果不在本scope读取。

技术报告/证据 commit [`9055410d72abbafec764821d308d874048a945cc`](https://github.com/HJY147/t44-dev-trace/commit/9055410d72abbafec764821d308d874048a945cc)。
[八段/十项报告](https://github.com/HJY147/t44-dev-trace/blob/9055410d72abbafec764821d308d874048a945cc/reports/reviews/functional-v7-campaign-3f51350ae1e5d89983dab69edebe3641804f54b3.md)；[机械证据](https://github.com/HJY147/t44-dev-trace/blob/9055410d72abbafec764821d308d874048a945cc/agents/reviewer/evidence/functional-v7-campaign/static-audit.json)。

本条只给精确执行技术准入，不发布APPROVE或business/performance/product/global/main/merge通过。其它source/draft/期限变化另审。
