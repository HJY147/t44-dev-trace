# Narrow diagnostic static-gate correction

Root reported exactdd320 off/on contracts+coverage passed but static failed on3 B110 try/except/pass in diagnostics.py28/51/115. Initial CI evidence remains root agents/coordinator/global-latency-ci/INITIAL_STATIC_FAILURE.log and original artifact hash/locations are bound in VALIDATION.PUBLIC.json; historical failure is not rewritten.

New isolated worktree branches from exactdd320. Only diagnostics.py changes: use explicit contextlib.suppress(Exception) around optional numeric counter bookkeeping, post-yield observer clocks/counts, and dispatch-ready measurement. Comments clarify boundaries. The span yield, wrapped business handler and all DB commit/body operations remain outside suppression; no finally return, globalBandit skip, nosec or CI threshold change. Existing failopen/exception object identity/context reset/PID privacy/incomplete header behavior unchanged.

Executed7 discovered diagnostic contract checks with strict markers:7passed. Executed full scripts/ci/static.py unchanged with T44_CI_REPORTS redirected only to this owner evidence directory: config/deployment static23tests/both repository Ruff scopes/full recursive backend Bandit all exit0. Bandit1.9.4 matches scripts/ci pin; results empty. This is local static+diagnostic verification, not a new exact full off/on CI run or performance fix. Root will perform one final off/on rerun. No cloud/SSH/native server/pressure action or extra functionality.

Commands and raw stdout/XML/static.json/BanditJSON are retained in this directory. Python3.12.10 differs from CI3.12.15 and does not replace CI. Product source frozen after this one-file fix.
