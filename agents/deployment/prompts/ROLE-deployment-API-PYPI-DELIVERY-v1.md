# ROLE-deployment-API-PYPI-DELIVERY-v1

本ID只归档本次实际派工，不冒作用户改码或提示词无意义演进。先按以下指令作最小外置渠道设计，再代码实现；root云执行仍另审，不由部署岗操作。

## 总协调实际派工原文

root已merge7a入integration（源C不变），限定TLS prepare/config审查通过，实际Ubuntu correct/wrongSAN guard已提交正在取回执。请现在完成最小外置API PyPI delivery生成helper，新分支树基当前root避免冲突；仅创建private 0700 runtime下新api-pypi-C.Dockerfile、同文件名+.dockerignore逐字copy原sidecar、manifest，O_EXCL0600不覆盖，验证sourceC HEAD+tracked clean；唯一Dockerfile差量是原pip install追加 --index-url https://mirrors.aliyun.com/pypi/simple/，保留no-cache-dir/require-hashes/全lock/base摘要，不能HTTP/trustedhost/额外index，不能改C目录。.dockerignore是重要输入边界C无根ignore，不得漏。helper只生成不build不network；输出old/new/ignore/lock hash和明确changed_channel_only/不是原Dockerfile字节构建。必要纯函数guard可内存，若test代码文件用tmp/deployment/849_xxx，851rootguard/850backendfixture/852tester已占。另给单独有界dockerbuildx API-only命令：policyv2同f910...，--platform linux/amd64 --load --tag t44-backend:local，外置Dockerfile+C context，不重建已好的web；1200s/云1320进程树+距17>=1440s，stdoutstderr留private logfile且最终只print退出+有界tail，避免长日志UI截断。未获root实执行回执前不宣称成功。
并通知接口归属：root已授权backend新增独立deployment/synthetic-fixture.py仅容器内3合成账号+公开RSA/AESGCM环境包，不改你既有文件。你不要接触852未公开资料，只有已发布crypto公用格式可由root中继。

## 设计与边界

固定产品C与三个输入SHA，纯transform只在原pip命令末增加一个HTTPS index选项，可精确反向恢复原bytes；sidecar逐字复制到外置同Dockerfile名称后缀。新runtime位于C树外且root0700、三输出0600/O_EXCL，不复用旧attempt。helper不下载/不build/不启动。单独文档API-only buildx命令有policyhash/源clean/manifest/ignore和stage deadline核验，1200/1320/1440边界、私有日志及有界尾。渠道改变需新构建证据，不叫原Dockerfile字节构建。

14项内存/临时合成guard和shell语法检查，不建test代码文件，不用849号；无Docker/网络/云/CI/账号/服务，也不接触backend fixture或852独立未公开资料。原601秒timeout失败和已build web保持，不宣API完成。
