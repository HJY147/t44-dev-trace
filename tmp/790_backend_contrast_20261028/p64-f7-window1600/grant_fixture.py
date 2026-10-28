"""Owned synthetic PUBLIC grant fixture, never a cloud authorization."""

import base64
import hashlib
import json


def pressure(control, mode="pressure"):
    result = dict(control)
    result.update(
        {
            "backend_image_id": "sha256:" + "1" * 64,
            "source_proof_sha256": "2" * 64,
            "source_file_count": 53,
        }
    )
    roles = {
        name: {
            "container_id": "3" * 64,
            "image_id": "sha256:" + "4" * 64,
            "running": True,
            "restart_count": 0,
        }
        for name in ("mysql", "rabbitmq", "api", "consumer", "web", "tls-gateway")
    }
    roles["scheduler"] = {"absent": True}
    grant = {
        key: result[key]
        for key in (
            "source_sha",
            "run_id",
            "binding_sha256",
            "namespace",
            "database",
            "api_workers",
            "backend_image_id",
            "source_proof_sha256",
            "source_file_count",
            "seed",
            "anchor_at",
            "stop_utc",
        )
    }
    grant.update(
        {
            "kind": "ROOT_P_" + mode.upper() + "_GRANT_V4",
            "admitted": True,
            "no_automatic_retry": True,
            "HTTP_authorized": mode == "pressure",
            "issued_at": "2026-10-28T04:00:00Z",
            "expires_at": "2026-10-28T16:00:00Z",
            "session_nonce": "5" * 48,
            "session_ttl_seconds": 600,
            "cohorts": [
                ["baseline1", 1, 20, 0],
                ["warmup40", 40, 5, 1],
                ["measure400", 400, 5, 41],
            ],
            "formal_performance_authorized": False,
            "roles": roles,
        }
    )
    raw = json.dumps(grant, sort_keys=True).encode()
    result.update(
        {
            "root_grant_b64": base64.b64encode(raw).decode(),
            "root_grant_sha256": hashlib.sha256(raw).hexdigest(),
        }
    )
    return result
