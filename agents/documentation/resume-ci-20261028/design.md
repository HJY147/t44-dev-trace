# 本轮 CI 证据收集设计

操作者为文档/CI汇总AI，不是独立黑盒验收岗。起点为总协调分支8c98eb13；只处理公开Actions原件、元数据和明确允许的已发表静态ZIP，不读取运行私密目录或独立测试内容，不触发、重跑或取消CI。

输入为product40636976337及Docker40636980359，均须核head=a12e9e70b963bacafda3242bb6d82e53ee912ff1。原始artifact ZIP保持下载字节，先核官方大小/SHA256、CRC、无重复/越界/符号链接，再只读解析JSON/XML。官方run日志ZIP另保原件，只有本地SHA时明确不冒官方digest。页面/摘要和源码中静态声明不能代替真实执行结果。

输出为records/ci/<run>/的原件与绑定清单、docs/reports/resume-ci-20261028-analysis.json和reports/final/resume-ci-20261028.md，以及本岗WORKLOG/module/handoff/prompt。先记录实际失败/缺失，再核修正轮次；不将两个源或PR merge-ref混算。

JUnit计数按唯一文件中的testcase node和结果核对。contracts标记子集与coverage全套是重叠执行，不能相加为唯一测试数。Python行覆盖按executed_lines/(executed+missing)计算，分支覆盖单列，coverage.py的混合percent_covered另标口径；前端使用coverage-final/json-summary并交叉核测试结果。Docker只证明日志中实际操作，不扩大为云性能或独立验收。
