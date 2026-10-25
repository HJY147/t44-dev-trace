# Independent performance v7 — PUBLIC result

Overall: **NOT_PROVEN**. One admitted formal-candidate attempt; no rerun or oracle change.

Original statuses: D01 **PASS** (18,086 requests); P01 **FAIL** (1,290 requests). The complete formal 400-client/600-second group count is **0**. All 19,376 actual HTTP requests returned complete HTTP200 responses; observed simultaneous requests never exceeded1. Inventory and preliminary GETs tagged warmup do not prove a 400-client load group. Steady requests, completed postconditions and formal metrics are0/null.

P01 original short error: `AssertionError: pagination completeness: 8424 expected 8401`. During85 pages of `GET /api/v1/projects/{project_id}/audit-events`, the observed total changed from8,401 to8,424 over4.09seconds. Returned and deduplicated rows both numbered8,424, with no duplicate IDs. This is a generic frozen pagination-completeness failure during serial preliminary queries, before a complete30-second load warmup or600-second steady group. The source of new audit rows, a product snapshot-consistency obligation and the responsible code/module remain **NOT_PROVEN**; no performance bottleneck is established.

The process ran from2026-10-25T10:00:14.557354Z to10:03:35.602137Z, before expiry; no hard/RSS stop. Exit0 is not acceptance.

The new encrypted evidence fully authenticated306,475 records and306,477 frames with no partial tail; every request begin/end matched. Original authority and frozen-tool hashes remain unchanged. Raw HTTP and keys remain private.

The bounded resource mirror stopped after copying the current source. Its5,998,336 bytes exactly match the source prefix SHA-256 `e055449a55efab6ef0636ac5e5d4b3f6615e889950e9af78c7f31f9741791051`:11,856 original lines, including2,479 null rows and9,377 numeric rows. No numeric-only view, zero fill, interpolation or gap replacement was made. Resource coverage is not evaluated because no formal steady group completed.
