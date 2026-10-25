"""Owned local broker/consumer lifecycle; preserve source, broker data and old receipts."""

import argparse
import hashlib
import importlib.util
import json
import os
from pathlib import Path
from uuid import uuid4


def context(run):
    bound = json.loads((run / "application-binding.json").read_text())
    path = run / "application-controller.py"
    if path.is_symlink() or hashlib.sha256(path.read_bytes()).hexdigest() != bound["application_controller_sha256"]:
        raise ValueError("BOUND_APPLICATION_CHANGED")
    spec = importlib.util.spec_from_file_location("fault_bound_application", path)
    app = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(app)
    module = app.controller(run)
    return app, module, app.binding(run, module)


def operate(run, action):
    app, module, bound = context(run)
    broker = module.broker_for(run)
    if action == "mq-stop":
        value = broker.stop()
        return module.receipt(
            run,
            "fault_mq_stop",
            success=value["success"],
            broker_receipt=value["receipt_id"],
            semantics="official graceful shutdown and observed owned VM/EPMD absence;not SIGKILL",
            broker_data_preserved=True,
        )
    if action == "mq-start":
        module.admitted()
        # Only retired identities from this newly owned run are moved. Never touch data/cookie.
        for role in ("rabbit", "epmd"):
            _record, actual = broker.owner(role)
            if actual is not None:
                raise ValueError("BROKER_ROLE_NOT_ABSENT")
        module.ports_free([module.PORTS[key] for key in ("amqp", "epmd", "distribution")])
        retired = []
        for role in ("rabbit", "epmd"):
            path = broker.state_path(role)
            if path.exists():
                module.private(path)
                target = path.with_name(role + "." + uuid4().hex + ".retired.json")
                if target.exists():
                    raise ValueError("NEW_RETIREMENT_PATH_REQUIRED")
                os.rename(path, target)
                retired.append(target.name)
        value = broker.start()
        return module.receipt(
            run,
            "fault_mq_start",
            success=value["success"],
            broker_receipt=value["receipt_id"],
            retired_record_names=retired,
            same_cookie_node_vhost_and_data=True,
        )
    if action == "consumer-stop":
        return module.receipt(run, "fault_consumer_stop", **module.stop_app(run, "consumer"))
    module.admitted()
    if module.owned(run, "guardian")[1] is None or broker.owner("rabbit")[1] is None:
        raise ValueError("LIVE_OWNED_BROKER_AND_GUARDIAN_REQUIRED")
    env = module.read(run / "secrets/application-environment.json")
    value = app.spawn(run, "consumer", [bound["python"], "-m", "t44.messaging"], env, bound, module)
    return module.receipt(
        run, "fault_consumer_start", success=True, pid=value["pid"], source_sha=bound["source_commit"]
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=("mq-stop", "mq-start", "consumer-stop", "consumer-start"))
    parser.add_argument("--run-dir", type=Path, required=True)
    args = parser.parse_args()
    os.umask(0o077)
    try:
        result = operate(args.run_dir, args.action)
        print(json.dumps(result))
        raise SystemExit(0 if result["success"] else 1)
    except (OSError, RuntimeError, ValueError, KeyError):
        print(json.dumps({"success": False, "error": "OWNED_FAULT_CONTROL_FAILED"}))
        raise SystemExit(1) from None
