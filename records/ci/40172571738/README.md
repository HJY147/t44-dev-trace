# Exact candidate development CI

[Product run 40172571738](https://github.com/HJY147/t44-dev-trace/actions/runs/40172571738) completed all four jobs successfully on `f237956ea23ecebd85d5e0c43fe20574adbb5139`: static, contracts, coverage and frontend. Application bytes equal production candidate `c8cea7e82805de5283ce67501769fa9a4efc1047`; the later change is the exact development query ledger adaptation from `5f55e09a75043343e376ecc7d96cc2ed98862b30`, not a product or independent-test change.

The coverage JUnit contains 562 backend cases, zero failures/errors/skips. Backend line coverage is 2642/2961 (89.23%), branch coverage 665/830 (80.12%). Frontend JSON reports 89/89 passed, zero failed/pending. Contract/integration/fault jobs separately ran 179/93/19 selected backend cases; these overlap the 562 and must not be added as new unique cases.

Four official ZIP artifacts were size/SHA-256 verified before safe extraction. Their original bytes and exact IDs/digests are preserved alongside `manifest.json`. The preceding candidate run's one stale query-ledger failure remains in records/ci/40171891359; it is not erased by this result.

Separate fresh-MySQL run 40172242303 on `6738c07b150da0df8554ba3b90d52e0cbc101fe6` completed six baseline low-level cases, six candidate low-level cases and seven candidate HTTP concurrency cases (86 HTTP responses, no cleanup error, zero checked-out connections before disposal). MySQL actually reported 8.4.13 / READ-COMMITTED; local native functional infrastructure separately uses 8.4.11. These observations cover the selected project/task lock paths, graph writer exclusion, predecessor freshness, capacity/manager-role freshness and CAS. The role race is manager-role downgrade, not an active=0 membership-revocation race. No global FK/secondary-lock deadlock-freedom claim follows.

This is development CI. Independent acceptance, a valid 400-client/600-second performance group, the 5100-line source-size gate, deployment billing and human-authored research-report requirements remain separate. Candidate source size is 6326, above 5100 by 1226.
