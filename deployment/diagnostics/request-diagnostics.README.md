# 请求分段诊断显式开关

`request-diagnostics.on.json`只含一个叶值：services.api.environment.T44_REQUEST_DIAGNOSTICS="1"。不改默认/base配置、镜像、workers、pool、卷、端口、CPU或阈值。只改主机.env不会把变量传入API；必须显式选择本overlay。此文件不自动执行任何命令。

overlay SHA256：`72d9785eeff21ae032b4c14fa3d6be8e79a3f78e4235bc90708d70557fb3f20d`。

使用前由root核：当前APP确切项目/工作目录/原配置全序列、已审新产品source/image、当前image的实际revision/runtime证明、原资源与原配置SHA。**旧p14 source13ac镜像不含本轮新诊断实现，不能仅加flag就冒充本分支。** CI模式通过也不等于该新镜像已构建或现场已替换。只使用本轮已审核并实际核验过的新镜像配置；本overlay不负责选择或改镜像。

## 手工enable模板（未执行）

以下变量必须是当前事实：BASE_CONFIG为原base文件，CURRENT_IMAGE_CONFIG为原本已核的新source镜像配置，DIAGNOSTIC_OVERLAY为此JSON绝对路径。若原部署还有其它配置文件，须按原序列完整重复-f，两个命令只在最后是否含诊断overlay不同；不得拿仓库默认Compose替代现场文件。先核每份输入SHA和原配置完整Env/Cmd/worker/pool等，渲染文件含敏感环境变量，应留在私密目录而不输出日志。

```sh
umask 077
sha256sum "$BASE_CONFIG" "$CURRENT_IMAGE_CONFIG" "$DIAGNOSTIC_OVERLAY"
docker --context default compose --project-directory "$CURRENT_WORKDIR" -p "$CURRENT_PROJECT" -f "$BASE_CONFIG" -f "$CURRENT_IMAGE_CONFIG" -f "$DIAGNOSTIC_OVERLAY" config --format json > "$PRIVATE_RENDERED_ON_JSON"
sha256sum "$PRIVATE_RENDERED_ON_JSON"
# root核渲染结果相较原配置只增加API的这一环境叶值，且输入/渲染SHA绑定当前准入后：
docker --context default compose --project-directory "$CURRENT_WORKDIR" -p "$CURRENT_PROJECT" -f "$BASE_CONFIG" -f "$CURRENT_IMAGE_CONFIG" -f "$DIAGNOSTIC_OVERLAY" up -d --no-deps --no-build --pull never api
```

最后命令是**操作者明确执行的**API容器环境更新，可能重建API容器；不是脚本自动执行。它不build/pull、不更新其它角色。禁止正在发压或有未核写入时执行；变更后重新核API ID/实际env flag1、新source image、原资源配置及健康，任何准入/七角色快照中相关ID应据实更新，不能继续用旧ID快照宣称当前通过。配置/环境/镜像漂移使旧hash绑定失效，须重新核验。

## 手工disable模板（恢复同一原配置序列，不含本overlay）

```sh
umask 077
docker --context default compose --project-directory "$CURRENT_WORKDIR" -p "$CURRENT_PROJECT" -f "$BASE_CONFIG" -f "$CURRENT_IMAGE_CONFIG" config --format json > "$PRIVATE_RENDERED_OFF_JSON"
sha256sum "$PRIVATE_RENDERED_OFF_JSON"
# root确认原配置及已审image默认未设置诊断1、配置漂移已排除后：
docker --context default compose --project-directory "$CURRENT_WORKDIR" -p "$CURRENT_PROJECT" -f "$BASE_CONFIG" -f "$CURRENT_IMAGE_CONFIG" up -d --no-deps --no-build --pull never api
```

移除overlay后应核实际API环境变量不存在或非1，恢复默认off；不得仅在主机unset后声称容器已关闭。没有改worker/pool或为诊断调整验收负载，不运行任何VMstop计时器。

## 解读与验证边界

后端说明：[FINDINGS](../../agents/backend/common-latency/FINDINGS.md)（实现来源7f445172）。diag-worker-pid是已明确授权的容器worker PID例外，缺PID为UNKNOWN；64指标/2048字符上界及diag-incomplete规则不变。缺marker、marker1或缺所需分段均UNKNOWN，不作0；嵌套wall spans不能相加，wall-CPU差不能单归DB锁。不会记录SQL/token/用户payload。

本次仅本地JSON解析并断言精确单叶结构与SHA；没有Compose渲染、环境应用、容器重建、VM访问或新CI触发。root正在等待的默认off/manualon全suite属于另一个精确source运行，不由本overlay任务重新触发。
