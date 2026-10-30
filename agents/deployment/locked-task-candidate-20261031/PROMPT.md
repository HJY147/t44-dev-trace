# 实际派工：部署AI，2026-10-31

协调者授权：固定部署岗接续，只离线/构建准备，先查已有构建避免重复；允许按准确13acb43a804e717e7485091895378511fe3d9b76触发GitHub镜像build，核source/image/runtimecontext/artifact hash并下载本地private目录。两VM用户已关闭，禁SSH/云操作/正式压测/任何自动停机；不能复用旧90b镜像冒新源。p13已消费，不复用run/material/grant。64CPU及400客户端/60秒预热/600秒稳态原阈值不变；不得额外对照压盘。不向用户请求现在开机。构建不是发布或验收准入。
