# 审核实际命令和范围

AI reviewer，2026-10-29。没有云/服务/Docker/实际HTTP/会话命令，未访问.runtime。

- `git show --stat 7936fe2a`、`git diff -- agents/backend/neutral-r30-cas/http_primitives.py agents/backend/neutral-r30-cas/prepare_http.py`及三个实际helper/source读取：核阶段红基线和代码，不将未提交内容当最终SHA。
- `python3 -B tmp/755_neutral_cas_review_r30/755_http_boundary.py > .../755_http_boundary.stdout 2> .../755_http_boundary.stderr`：初0.056s、最终0.060s，各2组全绿；五种HTTP outcome子例走真实parser+合成Connection，隔离import复现原source-free执行P1，绝无真实HTTP。初结果重命名initial保留。
- 内联Python AST比较`tmp/759_backend_neutral_r30/759_materials.py`与`tmp/756_backend_neutral_cas_r30/756_regression.py`：40 assert AST完全相同，结果755_assert_migration.json；未执行该全回归。
- `git show cb966f2117730d6b60227e85e30b6a8b0e3cc79a:agents/backend/neutral-r30-cas/code-manifest.PUBLIC.json`及内联Python：manifest0fc61e、18件全部hash/size，实际Git九py集合完全匹配；原17中仅http_primitives/prepare_http不同，加helper；关键两函数563→cb AST相同。原XML81/0fail/error，结果755_final_source_review.json。
- `git diff --name-only 686d79da cb966f21 -- backend frontend specs deployment agents/backend/neutral-r30 agents/backend/neutral-transport-r30 tmp/759_backend_neutral_r30 tmp/758_backend_transport_r30`：空。
- 已发表PUBLIC事实仅从root树records/cloud/r30window01读取summary与409-envelope-fields；未重读真实原会话、runtime私件或QA内部源。

路径预设的非产品命令失败保留说明：最初按惯例找不存在的contracts.py/escalations.py及RUNTIME_INTERFACE.md，exit1；真实文件通过rg清单定位contracts/__init__.py、RUNTIME_INTERFACE.PUBLIC.json；一次无匹配yaml glob和缺根pyproject搜索退出1/2。没有运行产品或修改文件，不把它们记CI结果。
