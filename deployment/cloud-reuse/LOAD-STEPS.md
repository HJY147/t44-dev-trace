# 纯synthetic Linux工具运行环境（非SUT验收）

原load-diagnostic.py SHA82e4与load-diagnostic-v2.py SHA603保留，均不执行。前者无crypto，后者错误假定sha256sum清单；root在执行前指出真实freeze为FILES.json，独立V3修正，**没有改805包/entry/增第13manifest**。本岗只读root明确批准PUBLIC的FILES.json与entry.verify定义，不读805私有、case或结果。

## 1. 离线依赖runtime，计时未开始

load-runtime.py SHAf30af6894f8fa1dab707115942c7e218c6177b13a27161e7a38936dd4f9b98c4固定两个已crypto证明base：backend935仅作dependencies阶段、officialPython作final，仅COPYsite-packages；不COPY/app/backend/specs/deployment，PYTHONPATH空/USER10001，无pip/RUN下载，不给旧officialPythonID重贴新runtime名称。固定新tag、DockerfileSHA、两base CIconfig/actualDescriptor、buildmetadata、本地新runtime.tar完整config/layer链与实际probe记录独立binding。单平台local tool关闭registryattestation并保存独立buildmetadata与完整crypto内容链，不把index候选随意当configID。

root实际build已成功（部署未操云），Python3.12.15/cryptography50.0.2/OpenSSL3.0.22，find_spec(t44)None、产品路径/appenv缺失为true。新的runtime-binding.json SHA479c968194d925e33c07ffcec4ac78eca4ed50945c901efbce25438a43844b42，alias t44-calibration-runtime:r9tools01，actual39820cc4fd3283abd2f3fd02388dc1c5982ba11dab898a82439721226c01005b，config89ced2fff1507b1a45b3db4fba389c359c8251bd0b1aaff30b9937a64e888cd0。这些是tool runtime，**不是原official image身份或产品通过**。

## 2. PUBLIC原12文件到云后准备V3

目录0555、文件0444/ownerroot，不存在link或额外文件。FILES.json原outerSHA cb4e8766b8d994c19f39ba7214cc5e1d8324bdbdbd6d23d72f8c7ee946a239e1；11源每项path/bytes/SHA；canonical commitment=sha256(json.dumps(files,ensure_ascii=False,sort_keys=True,separators=(comma,colon)).encode())，原值10b8137755cdd62cd75d1e0b36ef4772b331a858d1fe0a069f762fe47559e6ba。entry SHA5527842eb5c65f42b5b373bac61c43f5f767fdbb7fed207293dfb85f110d8ca3。

```sh
python3 /root/t44-r9/load-diagnostic-v3.py prepare \
  --runtime-helper /root/t44-r9/load-runtime.py \
  --runtime-binding /root/t44-r9/tool-runtime-01/runtime-binding.json \
  --runtime-binding-sha256 479c968194d925e33c07ffcec4ac78eca4ed50945c901efbce25438a43844b42 \
  --image-proof /root/t44-r9/image-proof.py --public-package APPROVED_PUBLIC_PACKAGE \
  --files-manifest-name FILES.json \
  --files-manifest-sha256 cb4e8766b8d994c19f39ba7214cc5e1d8324bdbdbd6d23d72f8c7ee946a239e1 \
  --output /root/t44-r9/cal805-01 --run-id r9cal805a
```

若这个目录已有真实成功回执，不重跑/覆盖，status/collect按原CID；新轮次另分配新目录。prepare只验证新runtime和包、建空data/control，计时未开始。

```sh
python3 /root/t44-r9/cal805-01/controller.py start --directory /root/t44-r9/cal805-01
```

此步才开始不超过900s的UTC+monotonic PID1 lifespan，restart=no/readonly/capdrop/user10001；严格2bind：新dataRW→/diagnostic、原PUBLIC包RO→/tool805，另仅/tmp tmpfs；无项目/runtime/appenv/docker.socket或SUT路径。host只映射127.0.0.1:18205，工具内部自己的loopback由批准包负责。根取得**已运行CID**（不是image），才调原已核冻结entry，示意：

```sh
docker --context default exec --detach --user 10001:10001 --workdir /diagnostic CID \
  python /tool805/entry.py launch --outdir /diagnostic/805-NEWNONCE --deadline EXACT_UTC
```

实际entry launch/status/collect命令及deadline/outdir由维护岗/root依据原接口确认；这不是任意exec接口。host entry --container CID只status/collect，不把宿主目录误当容器outdir。V3 controller仅prepare/start/status/stop，不替包写测试或解释结果。

```sh
python3 /root/t44-r9/cal805-01/controller.py status --directory /root/t44-r9/cal805-01
python3 /root/t44-r9/cal805-01/controller.py stop --directory /root/t44-r9/cal805-01
```

stop再次核CID、新runtime/config身份、run/proof/runtime/PUBLIC标签、恰好2bind与RW角色/loopback；正常10秒grace保留container/data，VM不动。900s到点自行退出，不能仅由“包已dispatch”预填完成/资源回收/校准通过。root已报实际prepare/start/dispatch成功，包deadline14:28:54UTC、容器最晚14:33:54UTC；本岗未看PUBLIC/sealed结果，实际collect和停止后验另记。
