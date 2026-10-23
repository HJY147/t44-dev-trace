"""Offline Compose schema and deployment safety invariants; not a container test."""

import json
import re
from pathlib import Path

import jsonschema
import yaml

ROOT = Path(__file__).resolve().parents[2]


def main() -> None:
    document = yaml.safe_load((ROOT / "compose.yaml").read_text())
    schema = json.loads((ROOT / "deployment/vendor/compose-spec.json").read_text())
    jsonschema.Draft7Validator(schema).validate(document)
    services = document["services"]
    assert {"mysql", "rabbitmq", "api", "consumer", "scheduler", "web", "migrate", "admin"} == set(services)
    assert all("ports" not in value for key, value in services.items() if key != "web")
    assert services["web"]["ports"] == ["127.0.0.1:${T44_HTTP_PORT:-8080}:8080"]
    assert {"mysql_data", "rabbitmq_data"} == set(document["volumes"])
    assert "service_healthy" in json.dumps(services["api"]["depends_on"])
    assert services["migrate"]["profiles"] == ["operations"]
    assert services["api"]["command"].count("4") == 1
    nginx = (ROOT / "deployment/nginx/nginx.conf").read_text()
    api = (ROOT / "deployment/nginx/api.conf").read_text()
    assert "try_files $uri $uri/ /index.html" in nginx
    assert "proxy_pass http://t44_api;" in api
    assert "error_page 413" in nginx and '"audit_id":null' in nginx
    payload = json.loads(re.search(r"return 413 '([^']+)';", nginx).group(1).replace("$request_id", "a" * 32))
    assert set(payload) == {"code", "message", "request_id", "audit_id", "current_version", "current_state", "original_error_code", "violations"}
    contract_path = ROOT / "specs/contracts/openapi.json"
    if contract_path.exists():
        contract = json.loads(contract_path.read_text())
        error_schema = {"$ref": "#/components/schemas/Error", "components": contract["components"]}
        jsonschema.Draft202012Validator(error_schema).validate(payload)
    log_format = next(line for line in nginx.splitlines() if "log_format minimal" in line)
    variables = set(re.findall(r"\$([a-z_]+)", log_format))
    assert variables == {"request_id", "status", "request_time", "upstream_response_time"}
    assert "$request_id" in log_format and "$request_time" in log_format
    print("Compose schema and deployment invariants passed; Docker/Nginx runtime NOT executed.")


if __name__ == "__main__":
    main()
