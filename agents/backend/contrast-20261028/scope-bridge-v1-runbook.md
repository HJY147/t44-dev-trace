# Scope桥v1：预装和一次实际回调模板

后端AI，2026-10-28；这份文件是运行模板，不是实际运行回执。当前没有新窗口、实际request或新rootgrant，所有null/尖括号必须由root下一轮真实PUBLIC材料替换并另存；禁止复用已结束nonce。仅root操作云和SUT，独立岗不接收本开发报告。旧失败材料不改。

## 先安装、先审，再启动独立会话

工具目录 `tmp/790_backend_contrast_20261028/scope-callback-bridge-v1/`。两宿主按顺序完整执行其中 `install-part01.PUBLIC.txt` 至 `install-part04.PUBLIC.txt`，新目的目录均为 `/root/t44-r9/scope-bridge-v1-01`。四命令长度分别11655、12976、15204、10495字节，另留300字节说明仍小于18000。每片拒绝覆盖；最后一片核所有九个模块的SHA/大小/0444模式，之前没有manifest不能运行桥。中途失败保留目录，禁止自动重试安装；root另审后选择新目录、重新生成安装材料。

manifest SHA：`4622154e098c7846ab9db0cd68993269d9ba924e9bcbf2f4c94b5a460253f07e`。交付分片SHA见 `delivery.PUBLIC.json`。宿主帮助命令不读SUT：

```sh
python3 /root/t44-r9/scope-bridge-v1-01/bridge_cli.py --help
python3 /root/t44-r9/scope-bridge-v1-01/bridge_owner_probe.py --help
```

先把公共配置 `configuration.template.PUBLIC.json` 填成新绝对路径文件，核原件再传入其SHA；空模板不能运行。字段含六原件path+SHA：grant、launch、supervisor、binding、neutral、admission。admission必须为本次真实 `ROOT_SINGLE_FUNCTIONAL_EXECUTION_RESERVED`，含实际root_grant_sha256、freeze、execution build、phase=functional、no_retry=true；它补足原launch/supervisor没有grant SHA的事实，不能凭旧grant推断新授权。原grant、launch和supervisor保持原文件字节，不重写冻结工具。

`app_phase_dir` 是新F实际phase绝对路径，`owner`由下方实际probe传入，`forbidden_key_shas`是本次初始材料接收key与operator证据接收key两种不同公钥的SHA（标准SPKI PEM，每64字符换行；request公钥会规范化后比较，不能换PEM折行绕过）。`status_path`可选本次PUBLIC状态文件；不能指向private。不填写私人账号、token、DSN、环境变量或独立用例。

在准入前，root还须预先准备读取新nonce、复制PUBLIC packet和搬运opaque回执的全部小命令；本桥没有跨机网络监听、SSH、公用服务或账号权限。传输时间算在原120秒内。未经一次完整受限端到端预演、实际双机时延预算核验及root限定审核，不直接把本地绿当下一次正式准入。

## LOAD：实际owner映射及新鲜authority

下面的路径/哈希是明确的运行时占位符，均不含私密参数；不能原样执行。root需在实际launch后取新容器完整ID、真实PUBLIC grant与launch，所有原件及配置已放在LOAD。`--output`须为未存在的新文件。probe读取Docker inspect/top、/proc stat/status和time namespace元数据，不读容器env、private、测试源码。

```sh
python3 /root/t44-r9/scope-bridge-v1-01/bridge_owner_probe.py \
  --container-id '<ACTUAL_FULL_CONTAINER_ID>' \
  --grant '<ACTUAL_GRANT_PUBLIC_PATH>' --grant-sha256 '<ACTUAL_GRANT_SHA256>' \
  --launch '<ACTUAL_LAUNCH_PUBLIC_PATH>' --launch-sha256 '<ACTUAL_LAUNCH_SHA256>' \
  --output '<NEW_OWNER_LOCATOR_PUBLIC_PATH>'

python3 /root/t44-r9/scope-bridge-v1-01/bridge_cli.py prepare \
  --manifest-sha256 4622154e098c7846ab9db0cd68993269d9ba924e9bcbf2f4c94b5a460253f07e \
  --configuration '<ACTUAL_CONFIGURATION_PUBLIC_PATH>' \
  --configuration-sha256 '<ACTUAL_CONFIGURATION_SHA256>' \
  --owner-locator '<NEW_OWNER_LOCATOR_PUBLIC_PATH>' \
  --owner-locator-sha256 '<ACTUAL_OWNER_LOCATOR_SHA256>' \
  --request '<ACTUAL_HANDOFF_DIR>/<ACTUAL_NONCE>.request.PUBLIC.json' \
  --request-sha256 '<ACTUAL_REQUEST_SHA256>' \
  --state-dir '<NEW_ABSOLUTE_LOAD_STATE_DIR>'
```

prepare打印PUBLIC `{folder,packet_sha256,packet_bytes,bridge_id,request_nonce}`，authority文件固定为返回folder下 `authority.packet.PUBLIC.json`，reservation为 `reservation.PUBLIC.json`。根只搬PUBLIC authority文件到APP并核打印的精确packet SHA；不能重写request/requestedUTC/nonce，不压缩改写已经生成的packet。相同grant+nonce只可reserve一次。实际owner locator含host与container两套PID及startticks；容器内PID9不能作为host PID。

## APP：原GEN与密封，root仅收opaque

APP必须已有本次F和匹配binding/controller/factory/compose/full-source-proof；root把PUBLIC authority.packet复制到新文件，保留LOAD打印的SHA。prepare到此的观测年龄最多30秒；剩余lease至少45秒，APP全部操作最多60秒；原GEN还要求本次binding stop至少600秒。超时保留前缀，不能用放宽期限或自动重跑过关。

```sh
python3 /root/t44-r9/scope-bridge-v1-01/bridge_cli.py provision \
  --manifest-sha256 4622154e098c7846ab9db0cd68993269d9ba924e9bcbf2f4c94b5a460253f07e \
  --packet '<COPIED_AUTHORITY_PACKET_PUBLIC_PATH>' \
  --packet-sha256 '<EXACT_LOAD_PACKET_SHA256>' \
  --state-dir '<NEW_ABSOLUTE_APP_STATE_DIR>' \
  > '<NEW_APP_RESULT_PUBLIC_PATH>'
```

PUBLIC输出 `PUBLIC_SCOPE_APP_RESULT_V1` 含有限receipt及opaque_b64，可由root原样搬至LOAD；不打印token/K或protected子进程输出。实际GEN使用binding内controller：首次scheduler-token后scheduler-start；已有同owner健康scheduler则scheduler-rotate后scheduler-start。启动前全context/source/project/iteration核验；回包前核真实scheduler image/labels/Running/restarts/mount/token文件SHA及原authstore中active credential的digest/project set/scope/expiry。原件里的project顺序在wire中保留，SQL内部排序只用于集合归属核验。

任何发生mutation后的失败留下phase的 `.inflight-or-quarantined`，后续请求拒绝；已发Docker/SQL动作可能迟到完成。禁止删除标记后直接重试，也不能假称回滚/零请求。root须保prefix，停下判断并在新的明确授权/环境安排下处理。

## LOAD：最终活性、pending和原子交付

root原样复制APP结果到LOAD新文件并核实际SHA。最后delivery仍独立重读所有PUBLIC原件、nonce pending、owned container/PID/startticks/PGID及本机UTC/monotonic截止；APP的alive不能代替LOAD实际检查。

```sh
python3 /root/t44-r9/scope-bridge-v1-01/bridge_cli.py deliver \
  --manifest-sha256 4622154e098c7846ab9db0cd68993269d9ba924e9bcbf2f4c94b5a460253f07e \
  --reservation '<ACTUAL_PREPARE_FOLDER>/reservation.PUBLIC.json' \
  --app-result '<COPIED_APP_RESULT_PUBLIC_PATH>' \
  --app-result-sha256 '<ACTUAL_APP_RESULT_SHA256>'
```

仅发布该request目录下 `<nonce>.sealed.PUBLIC.json`；同目录临时O_EXCL/no-follow、固定FD写入/fsync/chown后，最终检查再hardlink原子出现，无覆盖、无半JSON。LOAD不解密token，原冻结工具验RSA/MAC和业务。`PUBLIC_SCOPE_DELIVERED_NOT_BUSINESS_VERDICT`只说明交付，不是正式测试PASS。活性检查与文件发布并非一个OS原子事务；两次检查之间仍有观察窗口，回执明示。APP也不能证明LOAD在跨机执行期间持续存活。

## 公共依赖、边界和拒绝后处理

- 宿主：Linux root、Python3.10 stdlib、Docker默认context、可用/proc stat/status/NSpid/NSpgid/time namespace；time namespace必须与supervisor一致。Mac只跑本地假observer验证，实际host条件未证实。
- APP：本次实际F `binding.json`、controller.py/factory.py/compose.json（binding精确SHA）、phase.parent下actual-source-files.json（动态source_actual_proof_sha256/source_file_count字段）、data-only admin网络、实际本源backend image/config ID。禁止回退旧53字段名或旧namespace。
- 原backend image：Python3.12、原锁定cryptography/SQLAlchemy/PyMySQL及t44 Settings/Rows/token_digest/CLI；不临时pip，不改产品/DB schema/原GEN。密封编码器与原T15 c89文件逐字相同，RSA3072 OAEP-SHA256/AES-CBC+HMAC线格式不变。
- LOAD：实际冻结工具freeze33dd...5309e、execution e8ac...16ae、原120秒callback、rootgrant/launch/supervisor/admission、actual network隔离。新桥没有SUT准入权限，也没有撤销/ROOT_ACK实现；撤销由原工具auth/logout或另明确原CLI请求处理。
- 文件：根私密state目录0700；credential仍原10001/0600只读挂载；桥子进程stdout/stderr在private前缀，root不搬这些到UI。PUBLIC路径字符串可指向原private文件但本桥不读取其内容，唯一实际credential读发生在APP data-only容器内部。

失败只停止本次nonce，保真实prefix和inflight事实，无automatic retry/resume；旧会话自然结束后不补发。新F/新source/新image必须重新root准入和上下文pins，不复用本地合成grant。本地34桥检查和9安装检查不是双机、MySQL、正式独立验收或性能结论。
