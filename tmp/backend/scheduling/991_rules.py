import json
from datetime import UTC, datetime, timedelta, timezone
from pathlib import Path

import pytest
from t44.scheduling import (
    RuleConfigurationError,
    TimestampError,
    load_rules,
    parse_utc_timestamp,
    select_window,
)

RESOURCE = Path(__file__).parents[3] / "backend" / "t44" / "resources" / "escalation-rules.json"


@pytest.mark.parametrize(
    ("elapsed", "level", "code"),
    [
        (timedelta(days=-1, microseconds=-1), None, None),
        (timedelta(days=-1), 1, "临期"),
        (timedelta(microseconds=-1), 1, "临期"),
        (timedelta(0), 1, "临期"),
        (timedelta(microseconds=1), 2, "超期"),
        (timedelta(days=1, microseconds=-1), 2, "超期"),
        (timedelta(days=1), 3, "严重超期"),
        (timedelta(days=20), 3, "严重超期"),
    ],
)
def test_d001_exact_boundaries_and_highest_window(elapsed, level, code):
    rules = load_rules()
    end = datetime(2026, 10, 23, 12, 0, tzinfo=UTC)
    result = select_window(end + elapsed, end, rules)
    assert ((result.level, result.code) if result else (None, None)) == (level, code)
    if result:
        assert result.rule_version == 1
        assert result.recipient_roles == (
            ("assignee",) if level == 1 else ("assignee", "project_manager")
        )


def test_same_instant_is_deterministic_without_consuming_any_state():
    rules = load_rules()
    end = "2026-10-23T00:00:00.000001Z"
    first = select_window(end, end, rules)
    assert first.level == 1
    assert first == select_window(end, end, rules)
    assert first == select_window("2026-10-23T00:00:00.000001+00:00", end, rules)


@pytest.mark.parametrize(
    ("now", "end", "level"),
    [
        ("1000-01-01T00:00:00Z", "1000-01-01T00:00:00Z", 1),
        ("1000-01-02T00:00:00Z", "1000-01-01T00:00:00Z", 3),
        ("9999-12-31T23:59:59.999999Z", "9999-12-31T23:59:59.999999Z", 1),
        ("9999-12-31T23:59:59.999999Z", "9999-12-30T23:59:59.999999Z", 3),
        ("9999-12-31T23:59:59.999999Z", "1000-01-01T00:00:00Z", 3),
        ("1000-01-01T00:00:00Z", "9999-12-31T23:59:59.999999Z", None),
    ],
)
def test_supported_year_extremes_do_not_add_duration_to_end(now, end, level):
    result = select_window(now, end, load_rules())
    assert (result.level if result else None) == level


@pytest.mark.parametrize(
    "value",
    [
        datetime(2026, 1, 1),
        datetime(999, 12, 31, tzinfo=UTC),
        datetime(2026, 1, 1, tzinfo=timezone(timedelta(hours=8))),
        "2026-01-01T00:00:00",
        "2026-01-01T08:00:00+08:00",
        "2026-01-01T00:00:00.1234567Z",
        "2026-01-01T00:00:00.1234560Z",
        "2026-01-01T00:00:00.Z",
        "2026-01-01",
        "2026-01-01 00:00:00Z",
        "2026-02-30T00:00:00Z",
        "2026-01-01T00:00:60Z",
        "0999-01-01T00:00:00Z",
        "10000-01-01T00:00:00Z",
        None,
    ],
)
def test_invalid_or_overprecise_timestamp_is_rejected(value):
    with pytest.raises(TimestampError):
        parse_utc_timestamp(value)


def test_accepts_one_through_six_fractional_digits_without_rounding():
    assert parse_utc_timestamp("1000-01-01T00:00:00.1Z").microsecond == 100000
    assert parse_utc_timestamp("9999-12-31T23:59:59.123456+00:00").microsecond == 123456
    assert parse_utc_timestamp(datetime(1000, 1, 1, tzinfo=UTC)).tzinfo is UTC


def write_rules(tmp_path, raw):
    path = tmp_path / "rules.json"
    path.write_text(json.dumps(raw), encoding="utf-8")
    return path


def test_json_changes_window_thresholds_and_version(tmp_path):
    raw = json.loads(RESOURCE.read_text())
    raw["version"] = 2
    raw["rules"][0]["start_offset_seconds"] = -3600
    raw["rules"][2]["start_offset_seconds"] = 7200
    rules = load_rules(write_rules(tmp_path, raw))
    end = datetime(2026, 10, 23, tzinfo=UTC)
    assert select_window(end - timedelta(hours=2), end, rules) is None
    match = select_window(end + timedelta(hours=2), end, rules)
    assert (match.rule_version, match.level) == (2, 3)


@pytest.mark.parametrize(
    ("target", "field", "value"),
    [
        (None, "version", 0),
        (None, "version", True),
        (None, "version", ""),
        (None, "version", "version with spaces"),
        (None, "scan_interval_seconds", 0),
        (None, "scan_interval_seconds", True),
        (None, "scan_interval_seconds", 3601),
        (None, "rules", []),
        (None, "rules", {}),
        (0, "level", 2),
        (0, "level", True),
        (0, "label", ""),
        (0, "priority", 2),
        (0, "start_offset_seconds", 1),
        (1, "end_offset_seconds", -1),
        (2, "end_offset_seconds", -2),
        (0, "start_offset_seconds", -86400.0),
        (0, "start_offset_seconds", True),
        (2, "start_offset_seconds", 10**30),
        (1, "start_inclusive", "true"),
        (0, "start_inclusive", 1),
        (2, "end_inclusive", True),
        (0, "recipient_kinds", []),
        (0, "recipient_kinds", "assignee"),
        (0, "recipient_kinds", [1, 1]),
        (0, "recipient_kinds", ["unknown"]),
        (0, "recipient_kinds", [[]]),
    ],
)
def test_invalid_config_fields_fail_closed(tmp_path, target, field, value):
    raw = json.loads(RESOURCE.read_text())
    (raw if target is None else raw["rules"][target])[field] = value
    with pytest.raises(RuleConfigurationError):
        load_rules(write_rules(tmp_path, raw))


@pytest.mark.parametrize("raw", [[], None, {}, {"unknown": 1}])
def test_missing_or_unknown_root_fields_rejected(tmp_path, raw):
    with pytest.raises(RuleConfigurationError):
        load_rules(write_rules(tmp_path, raw))


def test_unknown_window_fields_rejected(tmp_path):
    raw = json.loads(RESOURCE.read_text())
    raw["rules"][0]["ui_threshold"] = 1
    with pytest.raises(RuleConfigurationError):
        load_rules(write_rules(tmp_path, raw))


@pytest.mark.parametrize("content", ["{", '{"schema_version":1,"schema_version":1}'])
def test_malformed_json_and_duplicate_keys_rejected(tmp_path, content):
    path = tmp_path / "broken.json"
    path.write_text(content)
    with pytest.raises(RuleConfigurationError):
        load_rules(path)


def test_missing_or_undecodable_file_preserves_error(tmp_path):
    with pytest.raises(RuleConfigurationError) as missing:
        load_rules(tmp_path / "absent.json")
    assert isinstance(missing.value.__cause__, FileNotFoundError)
    path = tmp_path / "bad-encoding.json"
    path.write_bytes(b"\xff")
    with pytest.raises(RuleConfigurationError) as invalid:
        load_rules(path)
    assert isinstance(invalid.value.__cause__, UnicodeDecodeError)
