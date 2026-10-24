# 两处静态样式修复设计（代码前提交）

精确基点dde39aa1c3ccf122caff5c24584ab69537d09007。原864/871文件由Git对象取得并与工作文件/各自blob逐字核对，原字节gzip+SHA另存。

只把864顶层prepared subprocess.run的stdout/stderr=PIPE改capture_output=True；只把871纯unit fixture的unused enumerate index改_index。先本地Ruff重现原两个诊断；不执行/import864。然后Ruff同两文件、内存compile不exec，归一AST证明这两个且仅这两个差量，并核本机stdlib subprocess.run的capture_output转换含义。原断言/案例/命名路径/豁免均不变，不跑已通过套件。

不改native application/runtime或任何活跃副本，不访问私密输入/4h副本、controller/服务/端口/OS信号。旧CI红和Git前像保留，新源码字节不得冒充旧运行归档。先设计commit再改代码，尽快给BE可合入SHA用于新候选CI，不重跑旧CI。
