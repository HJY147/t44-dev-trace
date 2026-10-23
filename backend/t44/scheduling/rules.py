"""Frozen rule schema, raw UTF-8 provenance, and data-driven window interpretation."""

import hashlib
import json
import re
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from pathlib import Path

from t44.contracts import violations

_TIMESTAMP = re.compile(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d{1,6})?(?:Z|\+00:00)")
_DEFAULT_RULES = Path(__file__).parents[1] / "resources" / "escalation-rules.json"


class RuleConfigurationError(ValueError):
    """Invalid or unsupported rule configuration."""


class TimestampError(ValueError):
    """Expected a UTC-aware timestamp in years 1000 through 9999."""


@dataclass(frozen=True)
class EscalationWindow:
    level: int
    label: str
    start: timedelta | None
    start_inclusive: bool
    end: timedelta | None
    end_inclusive: bool
    recipient_kinds: tuple[int, ...]
    priority: int


@dataclass(frozen=True)
class EscalationRules:
    version: int
    scan_interval_seconds: int
    windows: tuple[EscalationWindow, ...]
    effective_at: datetime
    raw: bytes
    raw_hash: bytes

    @property
    def rule_version(self):
        return self.version

    def snapshot(self):
        return json.loads(self.raw)


@dataclass(frozen=True)
class WindowMatch:
    rule_version: int
    level: int
    label: str
    recipient_kinds: tuple[int, ...]

    @property
    def code(self):
        return self.label

    @property
    def recipient_roles(self):
        return tuple({1: "assignee", 2: "project_manager"}[kind] for kind in self.recipient_kinds)


def _unique_object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise RuleConfigurationError(f"duplicate JSON key: {key}")
        result[key] = value
    return result


def load_rules(path: str | Path | None = None) -> EscalationRules:
    """Load exactly the frozen GET data shape; the hash covers original UTF-8 bytes."""
    try:
        source = (Path(path) if path is not None else _DEFAULT_RULES).read_bytes()
        raw = json.loads(source.decode("utf-8"), object_pairs_hook=_unique_object)
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise RuleConfigurationError(f"cannot load escalation rules: {exc}") from exc
    if violations({"$ref": "#/components/schemas/EscalationRule"}, raw):
        raise RuleConfigurationError("configuration does not satisfy frozen EscalationRule")
    if len({r["level"] for r in raw["rules"]}) != len(raw["rules"]) or len(
        {r["priority"] for r in raw["rules"]}
    ) != len(raw["rules"]):
        raise RuleConfigurationError("levels and priorities must be unique")
    integer_values = [raw["version"], raw["scan_interval_seconds"]]
    for item in raw["rules"]:
        integer_values += [item["level"], item["priority"], *item["recipient_kinds"]]
        integer_values += [
            item[k] for k in ("start_offset_seconds", "end_offset_seconds") if item[k] is not None
        ]
    if any(type(value) is not int for value in integer_values):
        raise RuleConfigurationError("integer configuration values must not be coerced")
    windows = []
    for item in raw["rules"]:
        start, end = (item[f"{bound}_offset_seconds"] for bound in ("start", "end"))
        if (
            (start is None and item["start_inclusive"])
            or (end is None and item["end_inclusive"])
            or (
                start is not None
                and end is not None
                and (
                    start > end
                    or (start == end and not (item["start_inclusive"] and item["end_inclusive"]))
                )
            )
        ):
            raise RuleConfigurationError("empty, reversed or ambiguously unbounded rule window")
        windows.append(
            EscalationWindow(
                item["level"],
                item["label"],
                None if start is None else timedelta(seconds=start),
                item["start_inclusive"],
                None if end is None else timedelta(seconds=end),
                item["end_inclusive"],
                tuple(item["recipient_kinds"]),
                item["priority"],
            )
        )
    return EscalationRules(
        raw["version"],
        raw["scan_interval_seconds"],
        tuple(sorted(windows, key=lambda w: w.priority)),
        parse_utc_timestamp(raw["effective_at"]),
        source,
        hashlib.sha256(source).digest(),
    )


def parse_utc_timestamp(value: datetime | str) -> datetime:
    """Strict UTC input, never truncate fractional digits or normalize unsafe year bounds."""
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
    """Subtract, match explicit bounds, then choose highest priority; no level switch."""
    elapsed = parse_utc_timestamp(now) - parse_utc_timestamp(planned_end)
    for window in reversed(rules.windows):
        lower = (
            window.start is None
            or elapsed > window.start
            or (elapsed == window.start and window.start_inclusive)
        )
        upper = (
            window.end is None
            or elapsed < window.end
            or (elapsed == window.end and window.end_inclusive)
        )
        if lower and upper:
            return WindowMatch(rules.version, window.level, window.label, window.recipient_kinds)
    return None
