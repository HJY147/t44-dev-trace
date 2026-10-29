# 已合入运维factory的最小语法修复设计

root反馈真实组合CI40636976337的static job122646082416：`deployment/cloud-reuse/app-campaign.py:133`已存在的`image = lambda role: images[role]["alias"]`触发E731。该助手于旧部署分支执行/留痕后才被主集成纳入全仓CI，因此不能修改排除清单或用noqa遮盖。

本次仅将同一函数作用域内的别名读取改为局部`def image(role): return images[role]["alias"]`，仍闭包捕获原`images`映射，调用时读同一映射，异常与返回不变，不复制/冻结或重排调用。输入输出为原compose_profile参数和完整Compose字典；不改变entry/worker/端口/网络/账号/TLS/容量及停止逻辑。

旧云端`/root/t44-r9/app-campaign.py`及原phase复制的factory仍为SHA256 daaf29d3b47ab266ae4546f001e322275db5c3c902c9f36f8b8a2528690af2ea；新repo文件必有新SHA。四个派生模板与其FACTORY_SHA继续pin旧daaf原件，本次不改它们或任何旧binding，不把新repo文件安装到旧云路径。根正在运输的新profile制品40637080936亦不因这次repo语法修复回写或换身份。

实现后仅做必要检查：用git历史精确daaf字节与新文件对照F4/P7/P16完整compose输出、映射访问顺序/异常；既有806_app_campaign本地保护检查；CI配置的Ruff。所有检查为运维工具开发验证，不是云或产品验收。原CI失败、旧运行版本留在历史，测试临时脚本续用本岗tmp793目录，不扩排除或noqa。
