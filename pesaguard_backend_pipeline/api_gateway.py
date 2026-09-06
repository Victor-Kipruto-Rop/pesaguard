"""Small but production-minded API gateway for Flask services.

The gateway centralizes authentication, versioning, tenant scoping, request
validation, correlation IDs, rate limiting, CORS, and response caching for the
PesaGuard backend.
"""

from __future__ import annotations

import hashlib
import logging
import re
import threading
import time
import uuid
from dataclasses import dataclass, field
from functools import wraps
from typing import Any, Callable, Dict, Iterable, Optional, Tuple, Union

from flask import Flask, g, jsonify, request

from pesaguard_backend_pipeline.rate_limiter import RateLimiter

logger = logging.getLogger("pesaguard.api_gateway")


@dataclass
class ApiGatewayConfig:
    """Configuration payload for the API gateway."""

    default_version: str = "v1"
    require_auth: bool = True
    allowed_origins: Iterable[str] = field(default_factory=lambda: ["*"])
    api_keys: Dict[str, Union[str, Dict[str, Any]]] = field(default_factory=dict)
    rate_limit_per_minute: int = 60
    allow_json_validation: bool = True
    cache_ttl_seconds: int = 60
    default_tenant: str = "default"

    def __post_init__(self):
        if isinstance(self.allowed_origins, str):
            self.allowed_origins = [self.allowed_origins]
        self.allowed_origins = [str(origin) for origin in self.allowed_origins]
        self._api_key_registry = self._normalise_api_keys(self.api_keys)

    @staticmethod
    def _normalise_api_keys(api_keys: Dict[str, Union[str, Dict[str, Any]]]) -> Dict[str, Dict[str, Any]]:
        normalised: Dict[str, Dict[str, Any]] = {}
        for tenant_id, value in (api_keys or {}).items():
            if isinstance(value, str):
                normalised[value] = {"tenant_id": tenant_id, "key": value}
                normalised[tenant_id] = {"tenant_id": tenant_id, "key": value}
            elif isinstance(value, dict):
                key_value = value.get("key") or value.get("value")
                if not key_value:
                    continue
                normalised[str(key_value)] = {
                    "tenant_id": str(value.get("tenant_id") or tenant_id),
                    "key": str(key_value),
                    "metadata": value,
                }
                normalised[str(tenant_id)] = {
                    "tenant_id": str(value.get("tenant_id") or tenant_id),
                    "key": str(key_value),
                    "metadata": value,
                }
        return normalised

    def resolve_api_key(self, api_key: Optional[str]) -> Optional[Dict[str, Any]]:
        if not api_key:
            return None
        return self._api_key_registry.get(str(api_key))


class _ResponseCache:
    """Thread-safe in-memory cache with TTL support."""

    def __init__(self):
        self._entries: Dict[str, Tuple[float, Any]] = {}
        self._lock = threading.Lock()

    def get(self, key: str):
        with self._lock:
            entry = self._entries.get(key)
            if entry is None:
                return None
            expires_at, value = entry
            if expires_at <= time.time():
                self._entries.pop(key, None)
                return None
            return value


    def set(self, key: str, value: Any, ttl_seconds: int):
        with self._lock:
            self._entries[key] = (time.time() + ttl_seconds, value)

    def clear(self):
        with self._lock:
            self._entries.clear()


_VERSION_SEGMENT_RE = re.compile(r"^/v\d+(/|$)", re.IGNORECASE)


class _VersionRoutingMiddleware:
    """Route versionless requests onto the gateway's default API version.

    Flask matches URLs *before* ``before_request`` hooks run, so a client that
    omits the version prefix (``GET /account``) would 404 before the gateway ever
    sees the request — unless the route was registered through
    :meth:`ApiGateway.route`, which adds an explicit alias. Wrapping the WSGI app
    covers routes registered directly on the Flask app as well, which is the
    common case when a gateway is attached to an existing service.

    The rewrite is conservative: it only fires when the original path matches no
    route *and* the version-prefixed path matches an existing one. Every other
    request — including genuine 404s — passes through untouched.
    """

    def __init__(self, wsgi_app: Callable[..., Any], url_map: Any, default_version: str):
        self.wsgi_app = wsgi_app
        self.url_map = url_map
        self.default_version = str(default_version or "").strip().strip("/")

    def _matches(self, path: str, method: str) -> bool:
        """Return True when ``path`` resolves to a registered route for ``method``."""
        try:
            adapter = self.url_map.bind("localhost")
            adapter.match(path, method=method or "GET")
            return True
        except Exception:
            return False

    def __call__(self, environ: Dict[str, Any], start_response: Callable[..., Any]):
        if self.default_version:
            path = environ.get("PATH_INFO") or "/"
            method = environ.get("REQUEST_METHOD") or "GET"
            version_prefix = f"/{self.default_version}"

            already_versioned = path.startswith(f"{version_prefix}/") or path == version_prefix
            if not already_versioned and not _VERSION_SEGMENT_RE.match(path):
                candidate = f"{version_prefix}{path}" if path != "/" else version_prefix
                if not self._matches(path, method) and self._matches(candidate, method):
                    environ["pesaguard.original_path"] = path
                    environ["pesaguard.rewritten"] = "1"
                    environ["PATH_INFO"] = candidate
                    logger.debug("Rewrote versionless request %s -> %s", path, candidate)

        return self.wsgi_app(environ, start_response)


class ApiGateway:
    """Flask API gateway extension."""

    def __init__(self, app: Optional[Flask] = None, config: Optional[ApiGatewayConfig] = None):
        self.config = config or ApiGatewayConfig()
        self._cache = _ResponseCache()
        self._validator_registry: Dict[str, Callable[[Any], None]] = {}
        self._rate_limiter = RateLimiter(default_max_per_minute=self.config.rate_limit_per_minute)
        self.app = None
        if app is not None:
            self.init_app(app)

    def init_app(self, app: Flask):
        self.app = app
        app.extensions["pesaguard_api_gateway"] = self
        app.wsgi_app = _VersionRoutingMiddleware(
            app.wsgi_app,
            app.url_map,
            self.config.default_version,
        )

        existing_before = app.before_request_funcs.get(None, [])
        if not any(getattr(func, "__name__", "") == self._before_request.__name__ for func in existing_before):
            app.before_request(self._before_request)

        existing_after = app.after_request_funcs.get(None, [])
        if not any(getattr(func, "__name__", "") == self._after_request.__name__ for func in existing_after):
            app.after_request(self._after_request)

        if not any(getattr(func, "__name__", "") == self._cors_preflight.__name__ for func in existing_before):
            app.before_request(self._cors_preflight)

    def _install_route_aliases(self, app: Flask):
        """Compatibility hook retained for older callers; route monkey-patching is
        intentionally avoided because it interferes with Flask's own setup checks
        and re-registration rules on shared applications."""
        app.wsgi_app = _VersionRoutingMiddleware(
            app.wsgi_app,
            app.url_map,
            self.config.default_version,
        )

    def _cors_preflight(self):
        if request.method == "OPTIONS":
            origin = request.headers.get("Origin")
            allowed_origin = self._resolve_cors_origin(origin)
            response = jsonify({"status": "ok"})
            response.status_code = 200
            response.headers["Access-Control-Allow-Origin"] = allowed_origin
            response.headers["Access-Control-Allow-Methods"] = "GET, POST, PUT, PATCH, DELETE, OPTIONS"
            response.headers["Access-Control-Allow-Headers"] = "Authorization, Content-Type, X-API-Key, X-Tenant-ID, X-Request-ID, X-Correlation-ID"
            response.headers["Access-Control-Max-Age"] = "600"
            return response

    @staticmethod
    def _versionless_alias(rule: str) -> str:
        if not rule or rule == "/":
            return rule
        match = re.match(r"^/(v\d+)(/.*)?$", rule)
        if not match:
            return ""
        suffix = match.group(2) or "/"
        if suffix == "/":
            return "/"
        return suffix

    def _resolve_cors_origin(self, origin: Optional[str]) -> str:
        if not origin:
            return self.config.allowed_origins[0] if self.config.allowed_origins else "*"
        if "*" in self.config.allowed_origins:
            return "*"
        if origin in self.config.allowed_origins:
            return origin
        return self.config.allowed_origins[0] if self.config.allowed_origins else "*"

    def _request_correlation_id(self) -> str:
        cid = (
            request.headers.get("X-Correlation-ID")
            or request.headers.get("X-Request-ID")
            or request.headers.get("X-Trace-Id")
            or str(uuid.uuid4())
        )
        request.environ["pesaguard.correlation_id"] = cid
        g.correlation_id = cid
        return cid

    def _resolve_api_version(self) -> str:
        path = request.path or "/"
        version_match = re.match(r"^/v(\d+)(?:/|$)", path)
        if version_match:
            return f"v{version_match.group(1)}"
        return self.config.default_version

    def _resolve_tenant(self, api_key_metadata: Optional[Dict[str, Any]]) -> str:
        tenant = (
            request.headers.get("X-Tenant-ID")
            or request.args.get("tenant_id")
            or (api_key_metadata or {}).get("tenant_id")
            or g.get("tenant_id")
            or self.config.default_tenant
        )
        if tenant:
            g.tenant_id = str(tenant)
            request.environ["TENANT_ID"] = str(tenant)
        return str(tenant or self.config.default_tenant)

    def _validate_json_request(self, payload: Any):
        if not self.config.allow_json_validation or payload is None:
            return
        if not isinstance(payload, dict):
            raise ValueError("JSON request body must be an object")
        if "amount" in payload:
            amount = payload["amount"]
            if isinstance(amount, bool) or not isinstance(amount, (int, float)):
                raise ValueError("amount must be numeric")
        if "currency" in payload and not isinstance(payload["currency"], str):
            raise ValueError("currency must be a string")

    def _before_request(self):
        if request.method == "OPTIONS":
            return None

        correlation_id = self._request_correlation_id()
        request.environ["pesaguard.request_id"] = correlation_id
        request.environ["pesaguard.api_version"] = self._resolve_api_version()
        g.api_version = request.environ["pesaguard.api_version"]

        api_key_value = (
            request.headers.get("X-API-Key")
            or request.headers.get("X-Api-Key")
            or request.headers.get("Authorization", "").replace("ApiKey ", "", 1).replace("Bearer ", "", 1).strip()
        )

        api_key_entry = self.config.resolve_api_key(api_key_value)
        if self.config.require_auth and not api_key_entry:
            return jsonify({"error": "missing_or_invalid_api_key", "message": "A valid X-API-Key header is required."}), 401

        if api_key_entry:
            g.api_key_tenant = self._resolve_tenant(api_key_entry)
            g.tenant_id = g.api_key_tenant
        else:
            g.api_key_tenant = self._resolve_tenant(None)

        if request.method in {"POST", "PUT", "PATCH"} and request.is_json:
            try:
                payload = request.get_json(silent=True)
                self._validate_json_request(payload)
                if request.endpoint and request.endpoint.endswith("reconcile"):
                    request.environ["pesaguard.request_payload"] = payload
            except ValueError as exc:
                return jsonify({"error": "invalid_request", "message": str(exc)}), 400

        route_validator = self._validator_registry.get(request.endpoint or "")
        if route_validator is not None:
            try:
                route_validator(request)
            except ValueError as exc:
                return jsonify({"error": "invalid_request", "message": str(exc)}), 400

        tenant_id = self._resolve_tenant((api_key_entry or {}))
        client_id = f"tenant:{tenant_id}" if tenant_id else f"ip:{request.remote_addr or 'unknown'}"
        allowed, status = self._rate_limiter.is_allowed(client_id, request.path)
        if not allowed:
            response = jsonify({"error": "rate_limit_exceeded", "message": "Too many requests. Please slow down."})
            response.status_code = 429
            response.headers["Retry-After"] = str(status.get("reset_in", 60))
            response.headers["X-RateLimit-Limit"] = str(status.get("limit", self.config.rate_limit_per_minute))
            response.headers["X-RateLimit-Remaining"] = "0"
            response.headers["X-RateLimit-Reset"] = str(status.get("reset_in", 60))
            return response

        self._cache.clear() if False else None

    def _after_request(self, response):
        origin = request.headers.get("Origin")
        allowed_origin = self._resolve_cors_origin(origin)
        response.headers["Access-Control-Allow-Origin"] = allowed_origin
        response.headers["Access-Control-Allow-Credentials"] = "true"
        response.headers["Access-Control-Expose-Headers"] = "X-API-Version, X-Correlation-ID, X-Tenant-ID, X-RateLimit-Limit, X-RateLimit-Remaining"
        response.headers["X-API-Version"] = getattr(g, "api_version", self.config.default_version)
        response.headers["X-Correlation-ID"] = getattr(g, "correlation_id", request.environ.get("pesaguard.correlation_id", str(uuid.uuid4())))
        response.headers["X-Tenant-ID"] = getattr(g, "tenant_id", self.config.default_tenant)
        response.headers["X-RateLimit-Limit"] = str(self.config.rate_limit_per_minute)
        response.headers["X-RateLimit-Remaining"] = "1"
        response.headers["Cache-Control"] = "no-store"
        return response

    def register_validator(self, endpoint: str, validator: Callable[[Any], None]):
        self._validator_registry[endpoint] = validator

    def route(self, rule: str, **options):
        def decorator(func):
            endpoint = options.get("endpoint") or func.__name__
            self.app.route(rule, endpoint=endpoint, **options)(func)
            alias = self._versionless_alias(rule)
            if alias and alias != rule:
                self.app.route(alias, endpoint=f"{endpoint}__versionless", **options)(func)
            return func

        return decorator

    def cached(self, ttl_seconds: Optional[int] = None, key: Optional[str] = None):
        def decorator(func):
            @wraps(func)
            def wrapped(*args, **kwargs):
                cache_key = key or f"{request.path}:{request.method}:{request.query_string.decode('utf-8', 'ignore')}:{hashlib.md5(repr(sorted(kwargs.items())).encode()).hexdigest()}"
                cached = self._cache.get(cache_key)
                if cached is not None:
                    return cached
                result = func(*args, **kwargs)
                self._cache.set(cache_key, result, ttl_seconds or self.config.cache_ttl_seconds)
                return result

            return wrapped

        return decorator


def _default_response_cache_key() -> str:
    return f"{request.path}:{request.method}:{request.query_string.decode('utf-8', 'ignore')}"


__all__ = ["ApiGateway", "ApiGatewayConfig"]
