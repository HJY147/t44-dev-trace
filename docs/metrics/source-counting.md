# 代码规模统计口径

使用cloc 2.10的非空、非注释物理行统计。主口径为已提交的应用Python、TypeScript、Vue、CSS和HTML：backend/t44、frontend/src及frontend/index.html。源码可读性与业务必要性优先，不拆行或填充功能凑数。

测试、部署及CI工具、权威DDL、契约与规则配置分别列组，不纳入3500～5100行的应用主口径。后端包内复制的OpenAPI和DDL不重复计算。依赖、生成物、构建目录、过程日志和报告不计算。脚本从指定HEAD归档选中的源码，避免把工作树中未提交内容误归属于该SHA；不读取独立验收内部资料。

工具来源为[cloc v2.10官方发布](https://github.com/AlDanial/cloc/releases/tag/v2.10)，下载脚本存本项目ignored运行目录；执行前校验GitHub发布资产SHA-256。复现：

```sh
curl --location --fail --output .agent-worktrees/.runtime/cloc-2.10.pl https://github.com/AlDanial/cloc/releases/download/v2.10/cloc-2.10.pl
python3 scripts/metrics/source_count.py
# 完整交付时加 --require-range，范围不符会返回非零。
```

原始逐文件计数、提交SHA、工具摘要及分组结果在records/metrics/source-count.json。cloc默认把Python三引号文档字符串视为注释，可能低估运行时多行字符串；Vue以文件计数器处理嵌入语言。这些限制保留，不为满足区间临时改统计参数。阶段计数不等于最终规模达标，待完整模块整合后重新统计。
