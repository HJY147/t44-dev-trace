# 772-v1 operation sequence

The coordinator may inspect only PUBLIC_FILES.json-listed files. It must not read PRIVATE, encryption keys, private inventory, source, cases or raw evidence. All preparation to date is offline; no Linux remote preflight, SUT request, VM start or purchase is authorized by this package.

1. Supply exact source-free Linux AMD64/Python 3.12 image digest/root and neutral connection/environment identity. Generate fresh actual sessions outside the tester and deliver the four real sessions/expiries and inventory privately. The whole new grant window includes setup, 60s warmup, 600s steady, bounded drain and postchecks. Existing old sessions/packets are never extended by the tester.
2. The coordinator copies the opaque runtime.772seal and PUBLIC bootstrap/launcher to LOAD. Only the independent tester delivers the capsule key directly to LOAD over the designated encrypted transport. Bootstrap is a finite standard-library installer; it decrypts into a new 0700 directory and never installs software. Root may hash/copy opaque bytes, but does not decrypt them.
3. Construct the new private environment and explicit allow=true one-time grant from the supplied schemas, bound to the exact environment/runtime/source/image/fixture/OpenAPI hashes. Publish only the grant's allowed neutral metadata. The default-false example is never changed into authorization by inference.
4. Only after all files and the collector are prepared, the coordinator can open the authorized <=1h billing window. Linux cgroup preflight and exactly one SUT cohort are invoked together using that single grant. A preflight failure consumes the grant and stops, with NP; there is no automatic second grant or run.

Example private installation, executed by the independent tester only after transport authorization:

```sh
python3 /private/public/bootstrap.py /private/public/runtime.772seal /private/capsule.key /private/runtime
```

Example container shape, with the exact actual image digest substituted before authorization:

```sh
docker run --rm --restart=no --name INDEPENDENT_NEW_RUN_ID \
  --network host --cpus 8 --memory 8g --memory-swap 8g --pids-limit 2048 \
  --ulimit nofile=4096:4096 --cap-drop ALL --security-opt no-new-privileges \
  --read-only --tmpfs /tmp:rw,nosuid,nodev,size=64m \
  --user "$(id -u):$(id -g)" \
  --mount type=bind,src=/opt/independent772,dst=/private \
  --entrypoint python3 EXACT_EXISTING_IMAGE_AT_SHA256 \
  /private/runtime/runtime.py run /private/environment.json /private/grant.json
```

Do not mount the SUT repository/source into LOAD. No dependency downloads are performed. The owned container/child group has an absolute UTC and monotonic stop. No other process/VM is controlled by the tester. The separate server collector uses the same run ID and UTC. After the run, the coordinator reviews shutdown/automatic-release settings separately from the performance metrics.

The independent tester recomputes metrics privately from the authenticated stream:

```sh
python3 /private/runtime/analyze.py /private/results/RUN_ID/evidence.772seal /private/results/RUN_ID/evidence.key /private/results/RUN_ID/recomputed.json
```

Retain encrypted evidence, key, receipt and failed prefixes. Only a full, continuous cohort can receive a performance metric verdict. The independent conclusion separately states unobserved MQ delivery, data-scale and transaction properties. No student research report or human action is fabricated.
