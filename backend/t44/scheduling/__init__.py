"""Internal escalation rules and explicitly constructed scheduler lifecycle.

Importing this package does not create or start a scheduler, scan storage or send messages.
"""

from .rules import (
    EscalationRules,
    RuleConfigurationError,
    TimestampError,
    WindowMatch,
    load_rules,
    parse_utc_timestamp,
    select_window,
)
from .runtime import build_scheduler, run_scheduler

__all__ = [
    "EscalationRules",
    "RuleConfigurationError",
    "TimestampError",
    "WindowMatch",
    "build_scheduler",
    "load_rules",
    "parse_utc_timestamp",
    "run_scheduler",
    "select_window",
]
