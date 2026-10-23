"""Versioned internal window selection; no eligibility, idempotency or delivery claim."""

import json
import re
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any

_TIMESTAMP = re.compile(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d{1,6})?(?:Z|\+00:00)")
_IDENTIFIER = re.compile(r"[A-Za-z0-9][A-Za-z0-9_.-]{0,63}")
_DEFAULT_RULES = Path(__file__).parents[1] / "resources" / "escalation-rules.json"


class RuleConfigurationError(ValueError):
    """Invalid or unsupported internal rule configuration."""


class TimestampError(ValueError):
    """Expected a UTC-aware timestamp in years 1000 through 9999."""


@dataclass(frozen=True)
class EscalationWindow:
    level: int
    code: str
    after_planned_end: timedelta
    inclusive: bool
    recipient_roles: tuple[str, ...]


@dataclass(frozen=True)
class EscalationRules:
    schema_version: int
    rule_version: str
    scan_interval_seconds: int
    windows: tuple[EscalationWindow, ...]


@dataclass(frozen=True)
class WindowMatch:
    rule_version: str
    level: int
    code: str
    recipient_roles: tuple[str, ...]


def _fields(value: Any, expected: set[str], label: str) -> dict[str, Any]:
    if not isinstance(value, dict) or value.keys() != expected:
        raise RuleConfigurationError(f"{label}: expected exactly {sorted(expected)}")
    return value


def _identifier(value: Any, label: str) -> str:
    if not isinstance(value, str) or _IDENTIFIER.fullmatch(value) is None:
        raise RuleConfigurationError(f"{label}: expected a 1..64 character identifier")
    return value


def _unique_object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise RuleConfigurationError(f"duplicate JSON key: {key}")
        result[key] = value
    return result


def load_rules(path: str | Path | None = None) -> EscalationRules:
    """Load schema 1 rules. I/O and malformed JSON errors retain their causes."""
    try:
        raw = json.loads(
            (Path(path) if path is not None else _DEFAULT_RULES).read_text(encoding="utf-8"),
            object_pairs_hook=_unique_object,
        )
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise RuleConfigurationError(f"cannot load escalation rules: {exc}") from exc
    raw = _fields(
        raw, {"schema_version", "rule_version", "scan_interval_seconds", "levels"}, "rules"
    )
    if type(raw["schema_version"]) is not int or raw["schema_version"] != 1:
        raise RuleConfigurationError("unsupported schema_version; expected 1")
    version = _identifier(raw["rule_version"], "rule_version")
    # D001 fixes cadence at 60 seconds; a future cadence change must revise this schema.
    if type(raw["scan_interval_seconds"]) is not int or raw["scan_interval_seconds"] != 60:
        raise RuleConfigurationError("schema 1 requires scan_interval_seconds=60")
    levels = raw["levels"]
    if not isinstance(levels, list) or len(levels) != 3:
        raise RuleConfigurationError("levels must contain exactly three ordered windows")
    windows = []
    for expected_level, value in enumerate(levels, start=1):
        item = _fields(
            value,
            {"level", "code", "after_planned_end_seconds", "inclusive", "recipient_roles"},
            f"level {expected_level}",
        )
        if type(item["level"]) is not int or item["level"] != expected_level:
            raise RuleConfigurationError("level values must be ordered 1, 2, 3")
        code = _identifier(item["code"], "code")
        seconds = item["after_planned_end_seconds"]
        if type(seconds) is not int:
            raise RuleConfigurationError("after_planned_end_seconds must be an integer")
        try:
            threshold = timedelta(seconds=seconds)
        except OverflowError as exc:
            raise RuleConfigurationError("window threshold exceeds timedelta range") from exc
        expected_inclusive = expected_level != 2
        if type(item["inclusive"]) is not bool or item["inclusive"] != expected_inclusive:
            raise RuleConfigurationError("window inclusivity must be true, false, true")
        roles = item["recipient_roles"]
        if (
            not isinstance(roles, list)
            or not roles
            or any(role not in ("assignee", "project_manager") for role in roles)
            or len(roles) != len(set(roles))
        ):
            raise RuleConfigurationError("recipient_roles must be unique known roles")
        windows.append(
            EscalationWindow(expected_level, code, threshold, item["inclusive"], tuple(roles))
        )
    if not (
        windows[0].after_planned_end
        < timedelta(0)
        == windows[1].after_planned_end
        < windows[2].after_planned_end
    ):
        raise RuleConfigurationError("window thresholds must be negative, zero, positive")
    if len({window.code for window in windows}) != 3:
        raise RuleConfigurationError("window codes must be distinct")
    return EscalationRules(1, version, 60, tuple(windows))


def parse_utc_timestamp(value: datetime | str) -> datetime:
    """Accept UTC datetime or strict UTC ISO text, never truncate fractional digits.

    This internal boundary is not an HTTP parser or evidence of database integration.
    """
    if isinstance(value, str):
        if _TIMESTAMP.fullmatch(value) is None:
            raise TimestampError("expected UTC ISO timestamp with at most six fractional digits")
        try:
            value = datetime.fromisoformat(value)
        except ValueError as exc:
            raise TimestampError("invalid calendar timestamp") from exc
    if not isinstance(value, datetime) or value.utcoffset() != timedelta(0):
        raise TimestampError("timestamp must be UTC-aware")
    if value.year < 1000:
        raise TimestampError("timestamp year must be in 1000..9999")
    return value.astimezone(UTC)


def select_window(
    now: datetime | str, planned_end: datetime | str, rules: EscalationRules
) -> WindowMatch | None:
    """Return only the highest current window, using subtraction to avoid overflow.

    No clock lookup, task state check, persistent de-duplication or notification is performed.
    At planned_end the task is still near due; one microsecond later it is overdue.
    """
    elapsed = parse_utc_timestamp(now) - parse_utc_timestamp(planned_end)
    for window in reversed(rules.windows):
        if elapsed > window.after_planned_end or (
            elapsed == window.after_planned_end and window.inclusive
        ):
            return WindowMatch(
                rules.rule_version, window.level, window.code, window.recipient_roles
            )
    return None
