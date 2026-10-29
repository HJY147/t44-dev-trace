#!/usr/bin/env python3
"""Public dispatch only. No SUT behavior/case/assertion is present here."""
import os,sys
from pathlib import Path
if len(sys.argv)<3 or sys.argv[1] not in ('offline-check','timer-gate','run'):
    raise SystemExit('usage: launch.py {offline-check|timer-gate|run} PRIVATE_RUNTIME [arguments]')
runtime=Path(sys.argv[2]).resolve()
if not runtime.is_file() or runtime.stat().st_mode & 0o077:
    raise SystemExit('private runtime required, chmod 700 or 600')
os.execv(sys.executable,[sys.executable,str(runtime),sys.argv[1],*sys.argv[3:]])
