# 来源和使用方式

设计阶段实际读取并运用 [OpenDesign 官方开源项目](https://github.com/nexu-io/open-design) 的本地 agent 技能、dashboard 模板和 apple / warm-editorial 设计系统参考。固定提交 `e03d5c23f308c39f4de7c057568df66c29a84385`，本地 package 版本为 0.25.1；逐文件摘要见 `sources.json`。

Open Design contributors 提供的内容使用 Apache-2.0；完整许可随附 `third-party/OPEN-DESIGN-LICENSE.txt`。frontend-design 由 OpenDesign 改编自 Anthropic 官方技能，其随附 Apache-2.0 许可保存在 `third-party/FRONTEND-DESIGN-LICENSE.txt`。critique 目录注明参考 alchaincyf/huashu-design；apple-hig 与 design-review 为上游发现入口，本阶段仅阅读说明，未安装或运行它们指向的完整工作流。

本项目自编 `DESIGN.md`、HTML 原型和生产 CSS；没有复制上游整站、品牌素材或界面截图。设计原则根据留痕项目、中文界面与用户指定米咖玻璃方向改写。没有启动 OpenDesign 桌面应用、使用 OpenDesign Cloud、调用 OpenDesign MCP 或外部模型服务。其本地文件被现有 agent 读取，再制作可点击原型、浏览器视检、形成设计提交，最后映射到 Vue。
