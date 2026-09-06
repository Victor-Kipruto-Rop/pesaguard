import json

from flask import Flask, jsonify

from pesaguard_backend_pipeline.api_gateway import ApiGateway, ApiGatewayConfig


def test_api_gateway_enforces_api_keys_version_headers_and_cors():
    app = Flask(__name__)
    config = ApiGatewayConfig(
        default_version="v1",
        require_auth=True,
        allowed_origins=["https://app.example.com"],
        api_keys={"tenant-a": "tenant-a-key"},
    )
    gateway = ApiGateway(app, config)

    @app.route("/v1/health")
    def health():
        return jsonify({"ok": True})

    client = app.test_client()

    missing_key = client.get("/v1/health")
    assert missing_key.status_code == 401

    allowed = client.get(
        "/v1/health",
        headers={"X-API-Key": "tenant-a-key", "X-Tenant-ID": "tenant-a"},
    )
    assert allowed.status_code == 200
    assert allowed.headers["X-API-Version"] == "v1"
    assert allowed.headers["X-Correlation-ID"]
    assert allowed.headers["Access-Control-Allow-Origin"] == "https://app.example.com"
    assert allowed.headers["X-Tenant-ID"] == "tenant-a"


def test_api_gateway_routes_versionless_requests_and_enforces_rate_limits():
    app = Flask(__name__)
    gateway = ApiGateway(app, ApiGatewayConfig(default_version="v1", require_auth=True, api_keys={"tenant-b": "tenant-b-key"}, rate_limit_per_minute=1))

    @app.route("/v1/account")
    def account():
        return jsonify({"tenant_id": "tenant-b"})

    client = app.test_client()

    ok = client.get("/account", headers={"X-API-Key": "tenant-b-key", "X-Tenant-ID": "tenant-b"})
    assert ok.status_code == 200
    assert ok.headers["X-API-Version"] == "v1"

    limited = client.get("/account", headers={"X-API-Key": "tenant-b-key", "X-Tenant-ID": "tenant-b"})
    assert limited.status_code == 429
    assert limited.headers["X-RateLimit-Limit"] == "1"


def test_api_gateway_validates_request_payloads_and_uses_tenant_from_key_metadata():
    app = Flask(__name__)
    gateway = ApiGateway(
        app,
        ApiGatewayConfig(
            require_auth=True,
            api_keys={"tenant-c": {"key": "secret-c", "tenant_id": "tenant-c"}},
            allow_json_validation=True,
        ),
    )

    @app.route("/v1/reconcile", methods=["POST"])
    def reconcile():
        return jsonify({"tenant_id": "tenant-c"})

    client = app.test_client()

    bad = client.post(
        "/v1/reconcile",
        headers={"X-API-Key": "secret-c"},
        data=json.dumps({"amount": "not-number"}),
        content_type="application/json",
    )
    assert bad.status_code == 400

    good = client.post(
        "/v1/reconcile",
        headers={"X-API-Key": "secret-c"},
        data=json.dumps({"amount": 1500, "currency": "KES"}),
        content_type="application/json",
    )
    assert good.status_code == 200
    assert good.headers["X-Tenant-ID"] == "tenant-c"
