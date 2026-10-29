# Actual narrow commands

AI reviewer, 2026-10-29. No cloud or service commands.

- `git show 36f9e9c9 -- agents/coordinator/r30-bounded/materials.py`: only time import, wait_until, two first-operation waits.
- `git show 36f9e9c9:agents/coordinator/r30-bounded/materials.py | shasum -a 256`: c2835a7fbc85c5c20c6b7936401f15710db5c7c615c2ae7aab4a08292d9b763c.
- `git diff 3be27131398a049f1a509918e5308f1bda7c8cec 686d79da3967123be7a3c24d6740d77be008c1bb -- agents/backend/neutral-r30 backend deployment`: empty.
- `/Users/yang/Desktop/nothing/软件开发大作业/.agent-worktrees/.runtime/database-scale-r29-venv/bin/python -B -m pytest -c backend/pyproject.toml tmp/758_backend_transport_r30/758_install.py -q -o cache_dir=/Users/yang/Desktop/nothing/软件开发大作业/.agent-worktrees/reviewer-neutral-r30/tmp/757_neutral_review_r30/transport-install-cache`: 2 passed in 0.05s, exit0; owner worktree cwd. Only synthetic local installer prefix, no service/HTTP.
- Inline `python3 -B` independently read exact manifest6 hashes/sizes, compared original790 Git bytes, rebuilt installer without writing owner files, parsed host3.10 AST, invoked exact wait_until with fake clock/sleep, parsed owner original XML7+2, asserted product/producer/deployment diff empty. All assertions passed; output retained in transport-schedule-review.json. This was not a rerun of crypto/TLS or an actual provider check.
