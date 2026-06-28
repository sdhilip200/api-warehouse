"""Turn an assess-produced endpoints spec into a dlt rest_api config dict."""
from __future__ import annotations


def _auth(spec_auth: dict, secrets: dict) -> dict | None:
    kind = spec_auth.get("type", "none")
    if kind == "none":
        return None
    if kind == "bearer":
        return {"type": "bearer", "token": secrets[spec_auth["token_env"]]}
    if kind == "api_key":
        return {
            "type": "api_key",
            "name": spec_auth["name"],
            "location": spec_auth.get("location", "header"),
            "api_key": secrets[spec_auth["token_env"]],
        }
    raise ValueError(f"unsupported auth type: {kind}")


def _resource(r: dict) -> dict:
    endpoint: dict = {"path": r["path"]}
    incremental = r.get("incremental")
    if incremental:
        endpoint["incremental"] = {
            "cursor_path": incremental["cursor_path"],
            "initial_value": incremental.get("initial_value"),
        }
        endpoint.setdefault("params", {})[incremental["param"]] = "{incremental.start_value}"
        write_disposition = "merge"
    else:
        write_disposition = "replace"
    return {
        "name": r["name"],
        "endpoint": endpoint,
        "primary_key": r.get("primary_key"),
        "write_disposition": write_disposition,
    }


def build_rest_api_config(spec: dict, secrets: dict | None = None) -> dict:
    secrets = secrets or {}
    client: dict = {"base_url": spec["base_url"]}
    auth = _auth(spec.get("auth", {"type": "none"}), secrets)
    if auth is not None:
        client["auth"] = auth
    paginator = spec.get("paginator")
    if paginator and paginator.get("type") != "single_page":
        client["paginator"] = paginator
    return {"client": client, "resources": [_resource(r) for r in spec["resources"]]}
