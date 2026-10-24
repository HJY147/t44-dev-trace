# Request-ID chain: source review and unimplemented technical proposal

Author backend AI. Fixed application C **0dfb55c2191200d947c5423fd9ee74bb0812cc5a**. Only read the explicitly published interim report; its SHA exactly matched8d1c4018354ac0a574f59b221f917b22c20587a89685357accc813d54fbb3361. No private driver/cases/raw/other852 material or developer private receipt read, no tester contact, cloud request, service, SQL, suite or CI execution.

## Proven scope and distinction

The released report records one HTTPS login200 with normalized header ID differing from body meta.request_id; frozen oracle stopped setup. It did not retain raw header lines. Both string fields exist separately in the original authority, but an explicit equality clause is not proven; retain **SUT requirement violation NOT_PROVEN**, frozen oracle unchanged, no functional/performance acceptance claim.

Root subsequently reported a separate developer observation17:36:48: unauthenticated GET/api/v1/projects, HTTP401, raw header count2, UUID80bc012a-f2b7-4924-966d-a570e5d6fe41 and32hex22fe81e2076196e6e0678d3a15ed7d3b. Backend did not execute it/read its private receipt. It proves two headers on that observed401 path only, not the earlier login count/all paths. Probe meta=null is not a mismatch finding: C errors.py21–31 emits **top-level request_id**, no success Meta; that body field was not measured.

## Actual source chain

| Source at fixed C / delivery helper | Exact role |
| --- | --- |
| backend/t44/api.py:203–213,225 | Middleware unconditionally generates str(uuid4()), passes same ID into Call; ignores incoming X-Request-ID as an authority. |
| backend/t44/api.py:231–258 | Success meta.request_id and API response X-Request-ID both use c.request_id. No distinct API generator in this branch. Error payload receives same current ID, including precommit500 at255. |
| backend/t44/services/errors.py:21–31; runtime.py:254–261,288–297 | Error ID is top-level; completed error replay replaces request_id with the current call ID, success replay keeps current envelope and separate original_request_id. Do not rewrite this to an old audit/original ID. |
| deployment/nginx/api.conf:5 | Web nginx generates its own $request_id and sends it as an upstream **request** header; API nevertheless generates its own UUID. |
| deployment/nginx/nginx.conf:26,32–33 | Server-level add_header X-Request-ID $request_id always is inherited by API locations, adding an independent web ID to the proxied **response**. No proxy_hide_header X-Request-ID exists in C. |
| deployment/web.Dockerfile:10–12 | Pinned nginx image actually copies those two C configuration files into its active paths. |
| deployment/tls-delivery.py:43–48; extended helper0ef2c2e same generated NGINX block | Extra TLS hop only proxies to web, sets Host/Connection/Forwarded-Proto; no request-ID generation/add/hide directive. It is not the source-code origin of the second ID. |

Nginx documentation says add_header adds response fields, default proxy suppression covers Date/Server/X-Pad/X-Accel rather than X-Request-ID, and $request_id is16 random bytes in hexadecimal. These facts support the static expectation of both API and web IDs on normal proxied responses; only root's separate401 observation proves an actual duplicate instance. Client normalization/order policy and the original login raw wire count remain unknown.

## Minimum proposed correction, NOT applied or admitted

Owner: deployment. Candidate changes only deployment/nginx/nginx.conf and deployment/nginx/api.conf; C backend/TLS config/DB/frozen schema/teacher requirement/oracle unchanged. Candidate image identity must be new even though backend bytes remain C.

At http level define one map from trusted **upstream response** ID to selected response ID, falling back to nginx's generated ID only when no upstream field exists. In API proxy include hide the upstream copy; server emits exactly one selected header. Conceptual directives:

```nginx
map $upstream_http_x_request_id $t44_response_request_id {
    "" $request_id;
    default $upstream_http_x_request_id;
}
# API proxy include:
proxy_hide_header X-Request-ID;
# Replace only the existing server response-ID directive:
add_header X-Request-ID $t44_response_request_id always;
```

Input/output: API's single generated UUID becomes the single public response header, matching current success Meta or top-level error ID without changing either payload. Local proxy413 has no upstream header and retains nginx ID matching its already-existing local error JSON. Static/proxy-origin responses retain a generated fallback ID. Keep proxy request header behavior, limits, timeout/routing/intercept policy and other security headers unchanged. Do not add location-level add_header blocks that drop inherited security fields. Do not make API trust raw client IDs or rewrite bodies. Ordinary proxy502 HTML/no JSON remains its existing behavior; this design does not claim to fix unrelated error-body contracts.

Technical value: one unambiguous client/body/audit correlation avoids client-library first/last/combined header differences and makes troubleshooting/replay current-ID semantics clearer. It is a transport/observability consistency improvement, not a retroactive teacher-mandated equality verdict. Existing web access log still uses its own edge ID; adding a separately named upstream ID there could improve hop correlation, but is optional separate scope requiring log-consumer review, not silently mixed into this minimum header candidate.

Risks: HTTP consumers relying on the old32hex edge ID will now receive application UUID for proxied responses (both satisfy the existing bounded string schema). Verify hide/map interactions on actual pinned nginx. Only accept the trusted upstream response ID, not $http_x_request_id. Recheck local413/empty-upstream/error paths and inherited headers; do not solve the equality goal by dropping required fallback headers, copying untrusted input, changing API auth, or overwriting old audit IDs. No code-size/performance benefit claimed; this may add config lines.

## Future bounded validation, separate authorization required

Use owned local fixtures/new candidate and raw header tuples, not normalized dict/get alone: API direct success/error; C web baseline vs new web through unchanged TLS; case-insensitive X-Request-ID count exactly1 after change; current body Meta/top-level error equality; repeated calls/new IDs; completed success/error replay current ID vs original metadata; spoofed client ID remains untrusted; local >2MiB413 fallback/body/header, application1MiB413, upstream absent/failure, static responses and inherited security fields. Keep credential bodies/Authorization out of public logs. Do not hit running C or private acceptance data, revise frozen oracle, contact tester or imply independent retest passed. Root must review/admit candidate first; deployment owner implements it on a new source and actual raw evidence is still needed.

## LOC work remains paused

Earlier task only read existing source_count.py/classifier, fixed C6310 receipt and source-budget-profile/runtime-plan candidate documents; no production or counter changes, no new cloc/benchmark/suite or saving has occurred. Existing C6310/5100 gap1210 is not canceled by this header proposal. Do not revive the previously rejected scan-dedup/AST route, or treat old unapplied validator-10 as achieved savings. The unfinished LOC design stays a separate task and does not enter new C identity.

Official sources: [response add_header](https://nginx.org/en/docs/http/ngx_http_headers_module.html#add_header), [proxy suppression](https://nginx.org/en/docs/http/ngx_http_proxy_module.html#proxy_hide_header), [request_id](https://nginx.org/en/docs/http/ngx_http_core_module.html#var_request_id), [upstream response fields](https://nginx.org/en/docs/http/ngx_http_upstream_module.html#variables), [map](https://nginx.org/en/docs/http/ngx_http_map_module.html#map). These are source semantics, not evidence of a new runtime request.
