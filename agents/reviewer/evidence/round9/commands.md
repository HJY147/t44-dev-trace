# 实际审核命令与原始输出

全部在 codex/review-size-round9 独立工作树执行，未改产品或运行云服务。

1. 读 AGENTS、review-protocol，git show c4b3/2914、git diff 043fc464 c4b3 -- 应用根。
2. git archive 两准确 SHA 的 backend/t44 和 tmp/backend/messaging，之后补齐 frontend/src/index。
3. Python预加载归档 t44.messaging.broker/facade，断言 __file__ 在归档根，打印SHA。
4. pytest -c backend/pyproject.toml -p no:cacheprovider 归档/tmp/backend/messaging -m 'not integration' --junitxml=.../messaging-bound.xml；39/39，23未选。
5. git archive 2914c7d 的 backend/t44、815_api_wire_boundary.py、probe.py 和两份基线oracle文件。
6. chdir API归档根、sys.path前置归档backend与根，预加载并核 api.py SHA；pytest12边界，api-wire-bound.log/xml。
7. 固定classifier筛应用、cloc2.10 hash等于bf5927...，仅对归档文件列表计量，messaging-count.json。

保留首次无import绑定log（不计）、backend-only与unfiltered not-main扫描（不作主指标）；
原工具读取曾遇不存在scripts/check-code-scale.py、pyproject.toml、ci.yml、database根及未匹配shellglob，
随后读取真实scripts/metrics/source_count.py、backend/pyproject.toml、product.yml和明确文件。
这些资料路径失败不冒称产品缺陷或已成功检查。
