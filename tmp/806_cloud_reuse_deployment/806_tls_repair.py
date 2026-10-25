"""TLS overlay preimage and security guards; no Docker/network/credentials."""

import copy
import importlib.util
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]


def module(name):
    spec = importlib.util.spec_from_file_location(
        name.replace("-", "_"), ROOT / "deployment/cloud-reuse" / name
    )
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def test_only_three_cache_directives_added_ssl_and_proxy_bytes_preserved():
    m = module("tls-repair.py")
    old = module("app-campaign.py").nginx()
    new = m.patch_config(old)
    expected = [
        "  fastcgi_temp_path /tmp/fastcgi_temp;\n",
        "  uwsgi_temp_path /tmp/uwsgi_temp;\n",
        "  scgi_temp_path /tmp/scgi_temp;\n",
    ]
    for line in expected:
        assert new.count(line) == 1
        new = new.replace(line, "")
    assert new == old
    with pytest.raises(ValueError, match="UNPATCHED_NGINX"):
        m.patch_config(m.patch_config(old))


@pytest.mark.parametrize(
    "old", ["no proxy marker", "  proxy_temp_path /tmp/proxy_temp;\n" * 2]
)
def test_unrecognized_preimage_refused(old):
    with pytest.raises(ValueError):
        module("tls-repair.py").patch_config(old)


def values():
    old = {
        "image": "proven:nginx",
        "user": "101:101",
        "read_only": True,
        "entrypoint": ["nginx"],
        "command": ["-g", "daemon off;"],
        "cap_drop": ["ALL"],
        "security_opt": ["no-new-privileges:true"],
        "tmpfs": ["/tmp"],
    }
    tls = copy.deepcopy(old) | {
        "volumes": [
            {
                "target": "/etc/nginx/nginx.conf",
                "source": "/new/nginx.conf",
                "read_only": True,
            },
            {
                "target": "/run/t44-tls",
                "source": "/phase/tls/server",
                "read_only": True,
            },
        ],
        "ports": [{"host_ip": "10.20.0.1", "published": "18445", "target": 8443}],
        "networks": {"edge": {}, "application": {}},
    }
    return old, tls, {"app_private_ip": "10.20.0.1", "tls_port": 18445}


def test_rendered_readonly_tls_exact_patch_accepted():
    old, tls, base = values()
    module("tls-repair.py").validate_tls(tls, old, base, Path("/new"), Path("/phase"))


@pytest.mark.parametrize(
    "change", ["uid", "readonly", "caps", "certificate", "publicport", "newnetwork"]
)
def test_security_certificate_or_endpoint_change_refused(change):
    old, tls, base = values()
    if change == "uid":
        tls["user"] = "0:0"
    elif change == "readonly":
        tls["read_only"] = False
    elif change == "caps":
        tls["cap_drop"] = []
    elif change == "certificate":
        tls["volumes"][1]["source"] = "/other/cert"
    elif change == "publicport":
        tls["ports"][0]["host_ip"] = "0.0.0.0"
    else:
        tls["networks"]["data"] = {}
    with pytest.raises(ValueError):
        module("tls-repair.py").validate_tls(
            tls, old, base, Path("/new"), Path("/phase")
        )
