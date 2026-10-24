# Request-ID proxy candidate: bounded design before implementation

Deployment AI; base `30afdefaeb7427ec3b582a85373d5143124e0581`; prompt `ROLE-deployment-REQUEST-ID-CHAIN-v1`. Backend's preceding technical design is `f9323e27c94c4453a5fe337c8b11a98558517d82:agents/backend/request-id-chain-design/design.md`. This candidate does not change or execute the running product C `0dfb55c2191200d947c5423fd9ee74bb0812cc5a`.

## Evidence and scope

Root relays a developer raw401 observation containing two response Request-ID fields; deployment has not read that raw or any independent cases, results, context or private files. The contract has no established explicit header/body equality clause: requirement violation remains NOT_PROVEN. This is a proposed transport correlation improvement, not a retrospective acceptance verdict.

Production delta is limited to `deployment/nginx/nginx.conf` and `deployment/nginx/api.conf`. At http scope map `$upstream_http_x_request_id` to the public ID only when it matches the entire lowercase canonical UUIDv4 shape actually emitted by C's `str(uuid4())`: `^[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$`. Quote the regex key for nginx configuration parsing. Default, including missing, empty, malformed, uppercase/non-v4 and comma-joined duplicate fields, is local `$request_id`. Do not accept arbitrary nonempty upstream strings or client input. In the API include hide all upstream `X-Request-ID` response fields; replace the existing server add_header value with the selected map variable. No location add_header is added, preserving security-header inheritance.

Keep API generation/client distrust, request-side header, local413 JSON/local ID, body limits, proxy routing/timeouts/intercept behavior, logs, static fallback/security headers, TLS, business and DB unchanged. Valid upstream IDs are an explicit trusted-upstream policy; invalid upstream payload IDs are not rewritten to invent body/header equality. A proxy502 retains its existing body behavior.

## Real nginx validation plan

No Docker/nginx is installed locally. Prepare a narrow branch-push GitHub Actions job on a fresh hosted Ubuntu24.04 runner, using exactly the C image `nginx:stable-alpine@sha256:47928bf67eb62a1863cb08d9ecb52d3e704304ba614eaee17884204677702951`, nonroot UID101, mounted byte-identical production config and a generated public static fixture. A stdlib synthetic upstream on the runner emits deliberate raw duplicate headers and generated UUIDs; no real application, DB, cloud/private network or credentials are used. Preserve raw response header tuples and synthetic bodies, command receipts, image identity, source hashes and failures as dedicated artifacts. Missing Docker, image pull, syntax or request failure must fail, not skip or simulate success.

First run `nginx -t` and baseline config from the immutable base; preserve a raw success showing the old exactly-two-header counterexample (the one-header assertion must fail). Then candidate `nginx -t` and raw assertions for success, error401/500, synthetic success/error replay (current ID versus separate original ID), spoofed client ID, missing/empty/invalid/non-v4/uppercase upstream IDs, duplicate same/different/mixed-case fields and explicit comma values, repeated unique requests, proxy-local >2MiB413/body correlation, upstream 1MiB413, upstream disconnect502, static and SPA fallback. Every candidate response checks exactly one ID and inherited three security headers. This validates real nginx behavior with fixtures; it is not real API auth/replay/TLS or independent acceptance/performance coverage.

Test driver must live under root-assigned numeric `tmp/deployment/` path; no new file until number allocated. Workflow is branch/path limited and independent from existing required gates. Job execution and results will be recorded only after real platform evidence; design/syntax checks alone do not prove nginx behavior. No cloud C/service change or workload interference.

## Official semantics checked this stage

- [map](https://nginx.org/en/docs/http/ngx_http_map_module.html#map): http context, case-sensitive regex and default fallback.
- [proxy_hide_header](https://nginx.org/en/docs/http/ngx_http_proxy_module.html#proxy_hide_header): suppress upstream response fields.
- [add_header](https://nginx.org/en/docs/http/ngx_http_headers_module.html#add_header): always and inheritance rules.
- [upstream variables](https://nginx.org/en/docs/http/ngx_http_upstream_module.html#variables): upstream response field access. Actual duplicate handling is subject to the pinned-runtime checks, not a Python string assertion.
