# source935可观测factory profile（不是正式production入口）

不改原P compose/env/binding770d.../controller/21:00UTC stop锚。PUBLIC只两文件：810_stage.py(8f0dbec80e168a8dbac7f3707b467d16c9146fe7937b7c5c2f6825b20bf966f6)、810_net_snapshot.py(dd776e1fe6c94aa005fa6b00734a6f8cebe54b24a9352917dbea7a771682552b)，不复制dir其他文件，不需session或业务packet。

```sh
python3 /root/t44-r9/diagnostic-overlay.py env-plan \
  --base-phase /root/t44-r9/campaign-935/p \
  --base-binding-sha256 770d774b715265ba517ea550aab5d001ecd8c04c58f3beb9cc558e752170ca06 \
  --sample-mode all --output /root/t44-r9/diag-env-935-01.json
```

只选原privateenv MYSQL_DATABASE/USER，HOSTmysql/PORT3306与原DSN生成规则相同，不改DATABASE_URL/T44_DATABASE。写精确10项DIAGJSON：ALLOWsource935-development-only/PRODUCT_SHA935/MODULE_SHA256/DATABASE/HOST/PORT/USER/OUTPUT/var/lib/t44-diagnostic/LIMIT10000/SAMPLE_MODEall。无口令/DSN内容输出，禁止额外env字段。

```sh
python3 /root/t44-r9/diagnostic-overlay.py prepare \
  --base-phase /root/t44-r9/campaign-935/p \
  --base-binding-sha256 770d774b715265ba517ea550aab5d001ecd8c04c58f3beb9cc558e752170ca06 \
  --public-tools-dir ROOT_APPROVED_TWO_SOURCE_DIR --diag-env /root/t44-r9/diag-env-935-01.json \
  --output /root/t44-r9/diag-profile-935-01
```

RO源/opt/t44-diagnostic+独立10001可写outputRW/var/lib/t44-diagnostic，两者来源都在新profile；PYTHONPATH/app/backend在前，API命令同7worker但为810_stage:app_factory --factory，标签明确不是生产entry，镜像/DB/锁/Auth/TTL不变。

```sh
python3 /root/t44-r9/diag-profile-935-01/controller.py config --profile /root/t44-r9/diag-profile-935-01
python3 /root/t44-r9/diag-profile-935-01/controller.py up --profile /root/t44-r9/diag-profile-935-01
```

逐条检查原timeractive和原文件SHA；up实际API/consumer/web/TLS，source935原image/configId、factoryCmd和labels实核，不能拿这个profile当正式entry成绩。status/stop-api同controller/action与profile，stop-api只停已核本诊断API，保DB/MQ；原hardstop仍认同sourceimage并保卷，不改旧锚。异常完整私有stderr在新receipts，不能打印全Compose或Env。

root实际up已成功：新profilebinding56d78db5dc30cbd08db1e29e93c466c0986969e78165ffc4ce370f07f21ef32e，实际7worker factory APIrunning；这是root官方回执转述，本岗无云操作，未读观测/driver/私有测试结果。

## CLI与CA中性接口

admin为operations profile，entrypoint原python -m t44.cli：

```sh
docker --context default compose --env-file /root/t44-r9/campaign-935/p/application.env \
  --file /root/t44-r9/campaign-935/p/compose.json --project-name t44-cloud-r9diag935-p \
  --profile operations run --rm --no-deps -T admin ORIGINAL_CLI_ARGS
```

wrapper清继承DOCKER_/COMPOSE_/T44_/MYSQL_/RABBITMQ_前缀，stdin/私有输出不在公开日志写Token。CA字段精确边界：**binding.tls没有ca_path**，只有ca_sha256/server_certificate_sha256/CA_private_key_mounted。prepare实际stdout.phases.p.ca_path已给/root/t44-r9/campaign-935/p/tls/ca.pem，用该已生成路径核SHA==binding.tls.ca_sha256(21dad4...)；可另建只读ca-receipt，不改冻结binding、不杜撰字段，不传ca.key。
