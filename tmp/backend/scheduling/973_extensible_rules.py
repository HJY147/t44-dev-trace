"""The generic interpreter needs no code change for a synthetic fourth rule."""

import hashlib
import inspect
import json
from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest
from t44.contracts import violations
from t44.scheduling import RuleConfigurationError, load_rules, select_window


def test_default_config_is_the_exact_frozen_get_shape_and_raw_hash():
    rules = load_rules()
    assert not violations({"$ref": "#/components/schemas/EscalationRule"}, rules.snapshot())
    assert rules.raw_hash == hashlib.sha256(rules.raw).digest()
    assert rules.version == 1 and rules.scan_interval_seconds == 60
    snapshot = rules.snapshot()
    snapshot["rules"].clear()
    assert len(rules.windows) == 3 and len(rules.snapshot()["rules"]) == 3


def test_fourth_rule_changes_only_one_configuration_and_uses_priority_not_level(tmp_path):
    source = Path(inspect.getsourcefile(select_window))
    original_code = source.read_bytes()
    config = load_rules().snapshot()
    path = tmp_path / "escalation-rules.json"
    path.write_text(json.dumps(config, ensure_ascii=False, indent=2) + "\n")
    before = {p.name: p.read_bytes() for p in tmp_path.iterdir()}
    config["version"] = 2
    config["rules"].append(
        dict(
            level=17,
            label="Synthetic extension, not adopted in production",
            start_offset_seconds=172800,
            start_inclusive=True,
            end_offset_seconds=None,
            end_inclusive=False,
            recipient_kinds=[2],
            priority=4,
        )
    )
    path.write_text(json.dumps(config, ensure_ascii=False, indent=2) + "\n")
    after = {p.name: p.read_bytes() for p in tmp_path.iterdir()}
    assert {name for name in before if before[name] != after[name]} == {"escalation-rules.json"}
    assert source.read_bytes() == original_code
    extended = load_rules(path)
    end = datetime(2026, 10, 23, tzinfo=UTC)
    assert select_window(end + timedelta(days=3), end, extended).level == 17
    assert select_window(end + timedelta(days=1), end, extended).level == 3
    # Reorder JSON and give lower numeric level the highest priority: no level switch/order rule.
    config["rules"][0]["priority"] = 5
    config["rules"][0].update(
        start_offset_seconds=None,
        start_inclusive=False,
        end_offset_seconds=None,
        end_inclusive=False,
    )
    config["rules"].reverse()
    path.write_text(json.dumps(config))
    assert select_window(end + timedelta(days=3), end, load_rules(path)).level == 1


def test_closed_single_instant_and_unbounded_window(tmp_path):
    config = load_rules().snapshot()
    config["rules"] = [
        dict(
            level=19,
            label="Synthetic instant",
            start_offset_seconds=0,
            start_inclusive=True,
            end_offset_seconds=0,
            end_inclusive=True,
            recipient_kinds=[1],
            priority=1,
        )
    ]
    path = tmp_path / "rules.json"
    path.write_text(json.dumps(config))
    rules = load_rules(path)
    end = datetime(9999, 12, 31, 23, 59, 59, 999999, tzinfo=UTC)
    assert select_window(end, end, rules).level == 19
    assert select_window(end - timedelta(microseconds=1), end, rules) is None


@pytest.mark.parametrize(
    "update",
    [
        {"start_offset_seconds": None, "start_inclusive": True},
        {"start_offset_seconds": 0, "end_offset_seconds": 0, "start_inclusive": False},
        {"priority": 2},
    ],
)
def test_invalid_extension_semantics_are_rejected(tmp_path, update):
    config = load_rules().snapshot()
    config["rules"][0].update(update)
    path = tmp_path / "rules.json"
    path.write_text(json.dumps(config))
    with pytest.raises(RuleConfigurationError):
        load_rules(path)
