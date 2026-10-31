"""Explicit opt-in config derivation; never edits source or runs/reloads Nginx."""

import argparse
import hashlib
import json
import re
from pathlib import Path


def derive(raw, expected_sha256, hop):
    if hashlib.sha256(raw).hexdigest() != expected_sha256:
        raise ValueError("SOURCE_CONFIG_HASH_MISMATCH")
    if hop not in {"web", "tls"}:
        raise ValueError("EXPLICIT_HOP_REQUIRED")
    text = raw.decode()
    if text.count("http {") != 1 or "t44_diag_" in text:
        raise ValueError("ONE_UNINSTRUMENTED_HTTP_CONTEXT_REQUIRED")
    # Preserve original minimal log and every existing access_log directive.
    if not re.search(r"log_format\s+minimal\s+escape=json\s+", text):
        raise ValueError("ORIGINAL_MINIMAL_LOG_REQUIRED")
    if re.search(r"access_log\s+off\s*;", text):
        raise ValueError("LOG_SCOPE_REQUIRES_EXPLICIT_REVIEW")
    snippet = """
    # Opt-in, 1/256 correlated response IDs (proxy-ID fallback). No URLs, bodies, cookies or full timing headers.
    map $upstream_http_x_request_id $t44_diag_response_id {
        default "-";
        "~^[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$" $upstream_http_x_request_id;
    }
    map $t44_diag_response_id $t44_diag_sample_key { default $t44_diag_response_id; "-" $request_id; }
    map $t44_diag_sample_key $t44_diag_sample { default 0; ~00$ 1; }
    map $upstream_http_server_timing $t44_diag_handler_ms {
        default "-";
        "~^app;dur=(?<t44_diag_handler_num>[0-9]+(?:\\.[0-9]+)?)(?:,|$)" $t44_diag_handler_num;
    }
    log_format t44_diag escape=json '{"hop":"HOP","request_id":"$request_id","status":$status,"request_time":"$request_time","upstream_time":"$upstream_response_time","response_request_id":"$t44_diag_response_id","upstream_connect_time":"$upstream_connect_time","upstream_header_time":"$upstream_header_time","upstream_status":"$upstream_status","connection_requests":"$connection_requests","handler_ms":"$t44_diag_handler_ms"}';
    access_log /tmp/t44-proxy-HOP.diag.jsonl t44_diag buffer=16k flush=1s if=$t44_diag_sample;
""".replace("HOP", hop)
    return text.replace("http {", "http {" + snippet, 1).encode()


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--enable", action="store_true", required=True)
    p.add_argument("--source", type=Path, required=True)
    p.add_argument("--source-sha256", required=True)
    p.add_argument("--hop", choices=["web", "tls"], required=True)
    p.add_argument("--output", type=Path, required=True)
    a = p.parse_args()
    raw = a.source.read_bytes()
    out = derive(raw, a.source_sha256, a.hop)
    with a.output.open("xb") as f:
        f.write(out)
    print(
        json.dumps(
            {
                "status": "DERIVED_NOT_ENABLED_OR_RELOADED",
                "source_sha256": a.source_sha256,
                "output_sha256": hashlib.sha256(out).hexdigest(),
                "hop": a.hop,
                "sample": "1/256",
                "original_bytes_unchanged": a.source.read_bytes() == raw,
            }
        )
    )


if __name__ == "__main__":
    main()
