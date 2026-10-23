# 需求与设计图示

8张图均来自两份报告的可编辑Mermaid源码，使用官方`@mermaid-js/mermaid-cli` 12.0.0和本机已有Chrome真实渲染。每张图保留`.mmd`、`.svg`、`.png`及原始工具日志；来源与产物SHA-256见[manifest](manifest.json)。

| 图 | 内容 | 成图 |
| --- | --- | --- |
| 需求1 | 产品边界与外部参与者 | [SVG](requirements-report-01-context.svg) / [PNG](requirements-report-01-context.png) |
| 需求2 | 角色与主要业务用例 | [SVG](requirements-report-02-use-cases.svg) / [PNG](requirements-report-02-use-cases.png) |
| 需求3 | 交付主流程 | [SVG](requirements-report-03-states.svg) / [PNG](requirements-report-03-states.png) |
| 需求4 | 阻塞与按原态解除 | [SVG](requirements-report-04-blocked.svg) / [PNG](requirements-report-04-blocked.png) |
| 设计1 | 模块与独立进程 | [SVG](design-report-01-architecture.svg) / [PNG](design-report-01-architecture.png) |
| 设计2 | 核心数据与事件关系 | [SVG](design-report-02-entities.svg) / [PNG](design-report-02-entities.png) |
| 设计3 | 成功、重放与独立拒绝事务 | [SVG](design-report-03-transaction.svg) / [PNG](design-report-03-transaction.png) |
| 设计4 | 扫描、outbox、MQ和降级通知 | [SVG](design-report-04-notifications.svg) / [PNG](design-report-04-notifications.png) |

总协调已查看8张独立PNG，核对中文显示、遮挡、箭头与本轮纠正的关系。此结论仅适用于成图；最终Word中的缩放、分页和表格仍需另行逐页渲染检查。主状态图第一次横向排列过长，改为纵向；阻塞往返边单列一图。M2原先7图、当时尚未渲染的历史不改写。

重建工具是[scripts/docs/render_diagrams.py](../../scripts/docs/render_diagrams.py)，需显式指定Node、Mermaid CLI和Chrome路径，重建后检查状态回到pending，不自动宣称已经人工看图。工具依据：[Mermaid CLI官方项目](https://github.com/mermaid-js/mermaid-cli)。
