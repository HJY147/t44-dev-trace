# 中性provider旧F本地包操作边界

本包source c5870926、3文件完整投递functional-provider-delivery.json，当前固定旧F/07:30窗口，**未获新F实际binding前不在后续08:15环境运行**。以下是供root复核的旧F运行形状，实际新F需另新工具版本，不能只换命令参数。

root在全新工具目录安装core/crypto/worker并逐helper-manifest核SHA。readonly helper/input目录及文件应10001所有、目录0500/文件0400；新输出父目录10001/0700。复制的schema仅T12-v2 PUBLIC件6db48a86054e974be1240cdd6cad8a17a2d5c038166dece32a149b5889f04e56，不能挂独立private/测试代码。新recipient公钥/nonce来自T12真实setup PUBLIC，不用旧52或P7传输RSA。

descriptor为ROOT_T12_PROVIDER_DESCRIPTOR_V1：binding_sha256、sut_identity（T12-v2的11字段）、recipient_nonce（48hex）、recipient_public_key_pem/recipient_public_key_sha256、host_public_proof_sha256、source_files（实际53行bytes/SHA/mode原顺序）、stop_utc、admin_networks=['data']、auth_store_resource_id（实际且含F DB名）、expired_subject/revocation_subject（m/d/d2/r/x内显式）、account_prefix（1–48安全字符）、fixture_ownership、provider_label、root_grant_sha256（材料阶段可null）。sut_identity来源于root实际source/archive/image/role/namespace/network/schema/MQ等已核证明，不手填猜测；单个descriptor hash不是云运行事实。

仅root通过既有F compose原data-only admin运行，不改服务配置或镜像：

```sh
docker --context default compose \
  --env-file /root/t44-r9/campaign-r28p7-01/f/application.env \
  --file /root/t44-r9/campaign-r28p7-01/f/compose.json \
  --project-name t44-cloud-r28p7gen01-f --profile operations \
  run --rm --no-deps -T --name t44-f-provider-material01 \
  --user 10001:10001 --entrypoint python \
  --volume ACTUAL_HELPER_DIR:/opt/provider:ro \
  --volume ACTUAL_PUBLIC_INPUT_DIR:/run/provider:ro \
  --volume ACTUAL_NEW_OUTPUT_PARENT:/diag-output \
  admin -B /opt/provider/790_provider_worker.py \
  --descriptor /run/provider/descriptor.PUBLIC.json \
  --descriptor-sha256 ACTUAL_PUBLIC_DESCRIPTOR_SHA \
  --schema /run/provider/schema.PUBLIC.json \
  --ca /run/provider/ca.pem --output-dir /diag-output/material01
```

上述ACTUAL标记不允许原样执行。root先核admin只有data网络、官方backend image身份、实际binding/fullsource53/schema/MQ、主API TTL3600及当前真实roles，原owned timer活跃；宿主等待timeout不得超过剩余原stop，超时按owned容器精确停并保前缀，不重试/重建账号。worker等待自然60，口令只内存/stdin，不输UI；写functional-material.T44FENV1+receipt.PUBLIC.json，root只move/hash密文。严禁cat任何私包或把解密结果交root模型。

之后仅actual测试scope request：root核实际launch/grant/原context；先由原controller scheduler-token（或已running时scheduler-rotate）精确project-id，scheduler-start实读F/scheduler-secrets/scheduler-token.json。provider还须私密只读核同文件token在原F auth store的actor2、scope/project IDs、expiry及真实应用receipt，才用该request另一RSA/nonce/context密封。纯crypto.scope函数只做线格式，**它本身不证明scheduler已应用**，不能把测试合成credential拿去云。撤销也只收到actual唯一session-id请求后原CLI revoke-session，setup交付保持active。
