# Independent checklist frozen before source inspection
1. Compare immutable original/candidate source identities and all changed modules.
2. Preserve 400 clients, 60 s warmup, 600 s steady measurement, metrics and all original assertions.
3. Preserve bounded 40 s post phase, 400 snapshots, full paginated histories, per-task schemas and assertions.
4. Verify errors, timeouts, incomplete coverage and partial failures cannot report PASS.
5. Inspect cancellation and cleanup of HTTP connections, tasks, process pools and evidence writer.
6. Verify complete exit status and evidence sealing on nonzero outcomes.
7. Independently execute useful offline positive/negative cases using own fixtures or authorized neutral replay data; no network/SUT.
8. Separate static evidence, local execution, unavailable Linux resource-limit behavior, and unperformed formal load acceptance. Do not modify historical records or frozen inputs.
