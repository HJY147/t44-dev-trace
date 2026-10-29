# R30 neutral-admin：固定运行接缝

操作者deployment AI；唯一正式行政入口由root明确采用此薄wrapper。无实际Docker/SQL/HTTP/云执行。代码阶段为749e8e877d0257f8cbe9ac4a789bb39e573d4a0c及8c73486440720506357ffa90efdb5b59cdd91028，wrapper最终19840B/SHA `8e9d024b7aa38692a633b620a23a27380d155ed7a8725f45c9ee25dac0fe4d9a`。原artifact、产品源、预算9e逻辑、GEN未改。

## 安装与固定host命令

`install-neutral-admin.PUBLIC.txt`是完整单条公共安装命令，raw8980B，整命令base64+256=12232<18000，installer SHA `493c6c85034465a4ca329b738077c45a96074b4301168a119c9edb67386484db`。它仅有限解码/核wrapper原bytes+SHA、O_EXCL安装到`/root/t44-r30/neutral-admin-wrapper-01/r30-neutral-admin.py`；不执行wrapper，不访问HTTP，不使用凭据。root准确SHA复审并完成窗口准入后才在APP提交；本岗没有执行。

```bash
python3 /root/t44-r30/neutral-admin-wrapper-01/r30-neutral-admin.py MODE \
  --phase-dir "$ACTUAL_NEW_PHASE" --binding-sha256 "$ACTUAL_BINDING_SHA256" \
  --profile-json "$ACTUAL_PROFILE/profile.json" --profile-sha256 "$ACTUAL_PROFILE_SHA256" \
  --code-dir "$FINAL_PRODUCER_DIR" --code-manifest "$FINAL_PRODUCER_DIR/code-manifest.PUBLIC.json" \
  --code-manifest-sha256 "$ROOT_REVIEWED_FINAL_PRODUCER_MANIFEST_SHA256" \
  --plan "$ORIGINAL_PRIVATE_PLAN" --intent "$ORIGINAL_PRIVATE_INTENT" \
  --import-receipt "$ORIGINAL_APP_IMPORT_RECEIPT" \
  --budget-receipt "$ORIGINAL_NEW_GEN_PROBE_RECEIPT" --budget-receipt-sha256 "$ORIGINAL_NEW_GEN_PROBE_SHA256" \
  --output-dir "$EXCLUSIVE_NEW_ATTEMPT_DIRECTORY"
```

MODE仅`seed/counts/service`，以及root后追加的`init-accounts`。init-accounts还须`--accounts "$ORIGINAL_PRIVATE_ACCOUNTS"`。没有任意命令、shell、SQL或新增scope参数。每次output-dir必须不存在，其parent必须真实owned0700目录；失败保留目录/原日志，不覆盖重试。

profile必须是root批准的R30准确SHA，带实际GEN hash、receipt03 adapter7efee30a...和预算9e98632f...；wrapper再从真实phase/controller.py验证同一GEN hash，通过其原phase_binding检查原binding raw/SHA/文件冻结。无凭据例：GEN run r30window01，project=t44-cloud-r30window01-p，database=t44c_r30window01_p，source=准确0b，stop=root真实G35。binding没有run_id字段，按project/db与profile.run_id配对解析，不能自造namespace或修改GEN规则。

## 原plan、路径和两类预算证据

- ROOT在写原plan时就填 `gen_binding.path="/neutral-input/binding.json"`、sha=真实原binding SHA。这个path是容器读取路径；wrapper拒绝原plan填host path，不会重写plan。target.binding_sha256也必须同一SHA。
- `source.actual_loaded_receipt_path`保留真实APP **host原import路径**，是来源元数据；子进程`--import-receipt`走固定容器路径并拿原bytes核SHA，guard不会按该host元数据path读取。wrapper的admission.PUBLIC.json另保存original_binding_path/original_import_receipt_path/original_probe_receipt_path，不冒容器路径是host原路径。
- `plan.budget.actual_admission_receipt_sha256`现存字段实际绑定原GEN **probe** receipt SHA，其kind必须为`actual-owned-mysql-budget-v4`。root从本轮GEN probe得到原文件后固定SHA写plan。wrapper不临时probe、不改plan/intents来换hash。
- wrapper拿真实9e `operation_lock`，在锁内重读原binding，核timer和backend alias，调用原runtime-env门禁和真实 `budget.admit`；admit会新measure并与原probe的binding/source/stop/MySQL身份/完整预算比较。返回值原样存在`admission.PUBLIC.json.actual_admit_return`，标明`r30-lock-held-live-readmission-v1`，它不是传给admin的原probe。flag/proof SHA都不替代外层锁。

## 固定容器argv、挂载、生命周期

三个producer模式唯一argv：

```text
python -B /neutral-code/admin.py MODE
 --plan /neutral-input/plan.json
 --intent /neutral-input/intent.json
 --budget-proof /neutral-input/budget.PUBLIC.json
 --import-receipt /neutral-input/backend-import-receipt.json
 --binding /neutral-input/binding.json
 --output /neutral-output/result
 --root-budget-admitted
```

通过原phase Compose `credential-admin` operation、`--entrypoint python --user 10001:10001 --rm --no-deps -T --pull never`运行。原服务必须同binding backend alias、仅data网络、never pull；实际alias必须仍匹配原actual/config ID。环境仍来自冻结application.env，既不`-I`清掉PYTHONPATH，也不改数据库密码。

code按root精确manifest逐bytes/hash核全部实际.py及声明JSON，排他copy到新stage code755/644，RO挂`/neutral-code`。支持明确的files=name→SHA+file_sizes布局，也支持显式rows。原plan/intent/probe/import/binding原bytes复制到inputs UID10001/0700、文件600，RO挂`/neutral-input`；不修改原输入。新output UID10001/0700挂`/neutral-output`。不把外层root0600锁挂给子进程，不新增子进程flock协议。

锁从实际admit前一直覆盖所有子进程退出、owned检查/必要timeout stop、prefix落盘以及最后窗口余量核验。子进程每次timeout至多180秒且保留600秒清理余量。timeout只stop同名、原image和三重owner/service/project label匹配的本次容器；身份/退出未证实即失败，不自动重试。stdout/stderr直接流到新logs0600私密原文件，不在公开stdout重放凭据或异常内容。

## init-accounts：正常CLI，先于seed

根确认的私有accounts输入是顶层manager/developer/reviewer三键，各值`{username:"synthetic-角色",password:null或实际私密值,user_id:null}`。**不是**producer的`accounts.init-input.template.PUBLIC.json` roles/password_stdin_file描述布局。新secret只在wrapper实际运行时生成，进入stdin及私密prefix，不出现在argv/env或公开stdout。

固定顺序manager→developer→reviewer，每个唯一CLI：

```text
python -B -m t44.cli init-user
 --username synthetic-ROLE --display-name synthetic-ROLE --password-stdin
```

三CLI在同一个真实9e锁/准入上下文中串行；官方0b CLI只INSERT，已有同名失败，不重置密码、不rollback/删除已完成账号。每个stdout/stderr原prefix分别保留。源码0b cli.py SHA `da88377aed1131fb82aea31ef2783e02af01c6b620518f3d1b9e8b01175112db` 的原main/parser实际测试序列化形状为`{"user_id":整数}`；wrapper严格接此形状并把真实ID写新output/accounts.initialized.private.json，原accounts输入不改。generated私密prefix在第一CLI前落盘，失败保留；中途失败不执行后续角色、不输出最终initialized成功文件。

seed/counts可在尚无projectIDs时按选库/真实空scope阶段执行；wrapper不要求未来40个IDs。后续后端从真实projects rows生成新的service/HTTP plan填真实IDs，run/source/原binding/T0/S/E/G/C不改。是否启动scheduler仍由其显式scope/token/start步骤负责，wrapper不启动它。

## root取回路径及实测界限

NEW_ATTEMPT_DIRECTORY下：

| 模式/证据 | host路径 |
|---|---|
| init | output/accounts.initialized.private.json |
| seed | output/result/seed-result.json |
| counts | output/result/counts.json |
| service | output/result/service.json；同result目录另有original-service.json/私密CLI logs |
| 外层原prefix | logs/MODE.stdout.private、MODE.stderr.private；init分别manager/developer/reviewer |
| 本次admit | admission.PUBLIC.json |
| 完成或失败 | completion.PUBLIC.json；CLI失败另有failure.PUBLIC.json，所有已有prefix保留 |

completion只给路径/源/namespace/数据库/绑定与credentials_disclosed=false，不给secret。三个admin模式实际结果必须为UID10001/600普通单链接文件才完成；假环境测试对此UID步骤明确用容器权限seam，不冒本机已跑Docker。

10项本地fake-env检查通过：真实9e flock/admit函数，host测试监视器在真实替身子进程生存期连续证实锁held（仅测试观察，无生产子进程协议），原CLI parser/main AST配持久化/哈希边界替身得到真实正负JSON形状；复制原input bytes不变，全部固定argv/result目录、部分初始化失败prefix、旧source/错namespace/错误code/失败预算拒绝。Docker/systemctl、容器UID和预算measure均是明确seam，不是实际DB观测。首次7项中测试替身漏`t44.persistence.accounts`模块导致1FAIL/1ERROR，保留后修正；首Ruff unused time失败保留，最终通过。

另按root实际producer0a34a81e9fb59abf6c500f5acbe284c053d1f903/manifest7c9d08a6...从Git原blob取17件，真实staging和固定argv纯mock smoke通过，未执行producer业务代码或SQL。若root后续producer因审核修复换最终manifest，应换成其准确新SHA再核，不因本次smoke接受旧candidate。没有任何云、HTTP或SUT结论。
