# Future APP HTTP execution seam — offline preparation only

Root reports both VMs economically stopped at 10:26Z. This delivery performs no cloud, Docker, SQL, HTTP, QA or session operation. Future execution requires root's separate approval of a real new run; no CLI flag supplies that authority. Old r30window01/materials.py/17-file producer and all historical artifacts remain unchanged. LOAD/QA retains source-free Python4f.

Runner: `deployment/cloud-reuse/r30-http-prepare.py`, 14842 bytes, SHA256 `0d5288b800cb56a0fed3cb9c28a5b83b8e200eacd73a7bfd84358b84440cc903`. Install alongside unchanged `r30-neutral-admin.py`, SHA256 `8e9d024b7aa38692a633b620a23a27380d155ed7a8725f45c9ee25dac0fe4d9a`; only its pinned private-file/staging/child helpers are reused, no SQL lock/admit function is called.

The actual tested future producer is commit `cb966f2117730d6b60227e85e30b6a8b0e3cc79a`, `agents/backend/neutral-r30-cas/`, 18 declared payload files (9 Python), original manifest SHA256 `0fc61e463692622f167548b7b00aed42fc18a58a0ae127317d6138e0a6136b8b`. The supplied manifest SHA is an explicit root pin, not a hard-coded historical producer version. All declared files require exact bytes/hash/source and all actual `.py` must equal declared `.py`; an extra verify-local.py is rejected. Staging copies only these18 plus the original manifest, code directories755/files644, mounted RO. Private input copies/output UID10001, directories700/files600; originals remain unchanged.

After future actual source/image/transfer/readiness approval, root writes immutable new plan and real accounts/service materials. `plan.gen_binding.path` MUST be `/neutral-input/binding.json`; original APP host provenance stays in `gen_binding.original_host_path` and `source.actual_loaded_receipt_path`. These are different roles. The runner also records the original host input paths in its receipt.

```sh
python3 "$FUTURE_OPS/r30-http-prepare.py" \
  --phase-dir "$ACTUAL_NEW_PHASE" --binding-sha256 "$ROOT_APPROVED_NEW_BINDING_SHA" \
  --code-dir "$FUTURE_PRODUCER18" \
  --code-manifest-sha256 0fc61e463692622f167548b7b00aed42fc18a58a0ae127317d6138e0a6136b8b \
  --plan "$ORIGINAL_NEW_PLAN" --accounts "$ORIGINAL_INITIALIZED_ACCOUNTS" \
  --service "$ORIGINAL_NEW_SERVICE" --import-receipt "$ORIGINAL_ACTUAL_IMPORT" \
  --ca "$ORIGINAL_NEW_CA" --output-dir "$NEW_EXCLUSIVE_ATTEMPT"
```

The output parent must be canonical, owned0700; attempt must not exist. Oldrun r30window01, changed source/namespace/binding, expired/misaligned packet or G/C, bad code, import or CA bytes refuse. Actual new GEN controller/factory and phase binding verify their original file chain; source is0b, original source manifest0c5b, bundleb2db and actual backend alias config8e. The current Docker inspect ID must equal original binding/import proven actual ID. With containerd, actual descriptor digest and verified descriptor/config/layer flags are checked separately from config8e; `.Id==config8e` is not required. Platform/labels/layer-count and official PYTHONPATH are checked; business DB/AMQP environment is refused. No image pull/retag/load occurs.

Exactly one existing owned edge network is used. Direct Docker run UID10001, readonly root, capsALL dropped, no-new-privileges, no `--env`, no env-file, no Compose application environment. Inherited official `PYTHONPATH=/app/backend` remains intact. Original plan/accounts/service/import/binding/CA copies mount at `/neutral-input`; RO code at `/neutral-code`; new writable output at `/neutral-output`.

First fixed child is `python -B /neutral-code/escalation_readback.py --check-runtime-only`. Its original `actual_image_identity_verified_by_probe=false` is preserved; wrapper observed actual Docker identity is separately recorded. Only then the second fixed child runs:

```text
python -B /neutral-code/prepare_http.py --plan /neutral-input/plan.json
 --accounts /neutral-input/accounts.json --service /neutral-input/service.json
 --ca /neutral-input/ca.pem --import-receipt /neutral-input/backend-import-receipt.json
 --binding /neutral-input/binding.json --output /neutral-output/result
 --root-admit-http-preparation
```

The flag is the producer's required input; it does not authorize a new cloud window or QA run. Original guard performs full plan/service checks before business HTTP. Runner has no QA/grant interface. It does not hold SQL admin lock during API preparation. Timeouts are at most300 seconds, re-evaluated after runtime probe, before packet cutoff/G with10 seconds reserved for owned-child termination. Cleanup only inspects/stops the new unique named child after ownership/image checks; no project-wide stop. Failure retains original private logs and result prefix. Stdout only status/receipt path/hash; `execution.PUBLIC.json` lists original paths and hashes, not secrets. Actual result directory is `NEW_EXCLUSIVE_ATTEMPT/output/result`; no successful child exit implies benchmark acceptance.

Executed locally: 5 meaningful external-seam tests using all18 actual Git blobs and original final manifest; fixed argv/staging permissions, Docker29 distinct actual/config plus DBenv refusal, source/namespace/oldrun/G/C/cutoff/expiry refusal, undeclared.py/badbytes refusal, runtime→HTTP success/timeout prefix retention. Producer business functions were not executed. Initial5 mock tests were green but had an incorrect C=G fixture: they are not real-contract admission evidence. Replacing it with actual G=T0+35/C=T0+40 produced2ERROR; retained `future-http-real-C-red.log`. Narrow fix now separately requires G35/C40, cutoff=S−150, D780–900, E≤G and E≤C−90; corrected5 tests green. Initial Python Ruff module missing and cached-offline Ruff6 findings retained; final offline Ruff green. Known C/G P1 is fixed locally; independent exact-SHA review and future real runtime remain pending. No current cloud admission.
