# P813 static prototype admission

AI reviewer, source baseline d9e971a631a970d59bdc96923f184c820f6de484.
This is a product-preserving candidate design, not a production patch or acceptance result.

Extract the identical durable scan row construction in `persistence/scans.py::ScanStore.start`
and `scheduling/facade.py::EscalationFacade._run` into one persistence-owned pure
`scan_run_values(*, run_key, rule_version, rule_snapshot, rule_hash, cutoff_at)` function.
Keep UoW ownership, duplicate races, error types, snapshot checks, and all lock paths unchanged.
The two callers supply the same evaluated expressions in their original order.

The script copies only those two product files into a scratch prototype, adds the helper
and one import, and replaces only the two dictionary expressions. It expands each helper
call back to the original dictionary AST and requires entire module AST equality after
removing the added definition/import. Compile syntax only; do not import application code.
Measure all before/after files with the unchanged cloc 2.10 release SHA from source_count.py.
No line packing, format changes, generated files, excluded relocation, live SQL, or tests.

The expected saving is small; record negative or zero results as measured. Even a positive
result cannot authorize owner implementation or count as reduced production size.
