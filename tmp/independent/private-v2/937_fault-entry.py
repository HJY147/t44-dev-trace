#!/usr/bin/env python3
"""Select only the original frozen real-service fault probes via versioned adapter."""
from pathlib import Path
import runpy
import sys
entry=runpy.run_path(str(Path(__file__).resolve().parent/'939_runtime-adapter.py'),run_name='independent_v2_adapter')
sys.exit(entry['run_adapter']('fault-all'))
