# Bootstrap公开源码权限修补：实施前设计

本轮只改部署脚本与本岗测试/记录，准确产品C不改；不操作云/服务/CI、原镜像标签或独立资料。root实际云回执另列为转述，不冒本岗云验证。

根因：现有全程umask077保护私有文件，但Git checkout据此产生公开tracked文件0600/目录0700；Docker COPY保留权限且归root，镜像UID10001/101读不到Python包/配置。AI实现与前轮AI审核漏查此边界，不能归为学生发现。

最小修补保留umask077。source阶段在精确C/clean后，按git ls-files --stage -z枚举stage0的100644/100755公开regular文件；先整体校验路径/type/非hardlink及其祖先目录非symlink，不walk，不chmod.git/.env/其他untracked。文件规范0644/0755，只有上述tracked父目录0755，source根0750；.env若已存在必须root-ownedregular0600，前后lstat快照相等，不读取/输出秘密。失败不自动回滚/重试；最终复核HEAD/clean。source既有目录复核也应用此规范。

Python逻辑内嵌bootstrap，保持原单文件经云助手可审relay；不增加对产品C中新helper的依赖。测试编号846仅在tmp/deployment/846_bootstrap_modes.py：提取内嵌函数、不执行shellsource/服务；纯临时Git fixture模拟umask077，对canonicalmodes/private.env/.git/untracked保持、symlink/hardlink/错误HEAD等必要边界。先在旧版断言缺少逻辑为红，后最小实现绿；实际root已手工修的C云目录不重跑。
