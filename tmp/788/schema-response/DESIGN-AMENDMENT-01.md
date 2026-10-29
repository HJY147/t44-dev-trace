# Explicit amendment before second execution

Frozen original design remains unchanged (SHA f48690390196ca1802da9ab380ab587bdaf6e66a34db21e9f21c555799d45734).

Run01 completed27 setup+4 response seed HTTP and stopped before timing. The exact pinned library2.22.2 compile raised KeyError('definition_rule') with detailed_exceptions=False; FastGate fell back to the original validator. A later injected-failure guard incorrectly assumed a compiled cache entry existed and raised KeyError. This is a compile/harness failure, not a false acceptance or a completed successful guard run. Run01 raw and both exact tool sources are retained.

Pure compilation of the same schema and exact version succeeded with detailed_exceptions=True. Run02 changes only that diagnostic option, explicitly checks that a compiled function exists before fault injection, and still exposes no library error details to callers. No compatibility keyword, original validator, error ordering, threshold, business function or SQL is weakened. If a false accept occurs, stop and seal FAIL; never time it.

To keep cumulative HTTP below200 across both runs, Run02 uses7 timed samples/path/phase:27 setup+4 seeds+16 warm+112 measured=159; cumulative31+159=190. SameA/B/B/A protocol and unprofiled handler CPU clock. The original8-sample design is not rewritten into having been executed.
