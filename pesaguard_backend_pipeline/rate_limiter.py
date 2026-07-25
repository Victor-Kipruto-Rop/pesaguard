"""Rate limiting for bulk operations to prevent abuse.

Token Bucket Implementation:
  - Each (user_id/IP, endpoint) pair gets a token bucket
  - Tokens are refilled at configurable rate (e.g., 30 per minute = 0.5 tokens/sec)
  - Each request consumes 1 token by default
  - If no tokens available, request is rejected with 429 Too Many Requests

Webhook Rate Limiting:
  - Applied in app.py::enforce_webhook_security() before_request hook
  - Uses source IP as user identifier (Daraja callbacks are not authenticated)
  - Default: 30 requests/min per IP (configurable via PESAGUARD_WEBHOOK_RATE_LIMIT_PER_MINUTE)
  - Protects against DDoS and accidental webhook storms

Dashboard Rate Limiting:
  - Can be applied per-endpoint using @rate_limit decorator
  - Uses authenticated user ID when available, falls back to IP

Environment Variables:
  - PESAGUARD_WEBHOOK_RATE_LIMIT_PER_MINUTE: max requests per minute for webhook endpoint (default 30)
  - Rate limiter is instance-scoped; multiple workers should use Redis/external store for distributed rate limiting
"""

import threading
import time
from typing import Dict, Tuple
from functools import wraps
from flask import request, jsonify, g
from collections import defaultdict

# A bucket that hasn't been touched for this long has, by construction,
# already refilled to its max (the refill window IS one minute — see
# is_allowed's refill math) — so it's safe to drop and recreate fresh next
# time it's used, with identical resulting behavior. Used for lazy eviction
# below to bound memory growth.
_BUCKET_IDLE_TTL_SECONDS = 60


class RateLimiter:
    """Token bucket rate limiter for API endpoints."""

    def __init__(self):
        # key: bucket_key, value: (tokens, last_refill_time)
        self.buckets: Dict[str, Tuple[float, float]] = {}
        self.max_tokens_per_minute = 10  # default
        self.refill_rate = 10 / 60  # tokens per second
        # FIXED: is_allowed() previously did an unguarded read-modify-write
        # on self.buckets. Under a multi-threaded WSGI worker, two concurrent
        # requests for the same bucket key could both read the same token
        # count before either wrote back, letting more requests through than
        # the configured limit. This lock makes each check-and-consume
        # atomic.
        self._lock = threading.Lock()

    def set_limits(self, max_requests_per_minute: int, endpoint: str = None):
        """Set rate limit for an endpoint.

        Note: `endpoint` is currently unused — limits apply instance-wide to
        every bucket this limiter manages, not per specific endpoint name,
        even though individual endpoints get separate bucket entries (see
        get_bucket_key). Reserved for future per-endpoint configuration.
        """
        self.max_tokens_per_minute = max_requests_per_minute
        self.refill_rate = max_requests_per_minute / 60

    def get_bucket_key(self, user_id: str, endpoint: str) -> str:
        """Generate bucket key from user ID and endpoint."""
        return f"{user_id}:{endpoint}"

    def _evict_stale_buckets(self, current_time: float) -> None:
        """Drop buckets idle long enough to have fully refilled anyway.

        FIXED: buckets were never removed, so every unique (user_id/IP,
        endpoint) pair ever seen created a permanent dict entry for the
        life of the process — a slow, unbounded memory leak, worst for the
        webhook limiter (keyed by client IP, internet-facing, unauthenticated).
        Safe to evict here specifically because a bucket idle longer than the
        refill window has already conceptually refilled to max — recreating
        it fresh next access produces identical behavior to keeping it around.
        """
        stale_keys = [
            key for key, (_, last_refill) in self.buckets.items()
            if current_time - last_refill > _BUCKET_IDLE_TTL_SECONDS
        ]
        for key in stale_keys:
            del self.buckets[key]

    def is_allowed(self, user_id: str, endpoint: str, tokens_required: int = 1) -> Tuple[bool, Dict]:
        """Check if request is within rate limits."""
        bucket_key = self.get_bucket_key(user_id, endpoint)
        current_time = time.time()

        with self._lock:
            # Opportunistic cleanup — cheap at pilot scale; if this dict
            # grows large enough for O(n) eviction to matter, that's the
            # signal to move to the Redis-backed store the docstring already
            # calls out for distributed/high-scale deployments.
            self._evict_stale_buckets(current_time)

            if bucket_key not in self.buckets:
                self.buckets[bucket_key] = (self.max_tokens_per_minute, current_time)

            tokens, last_refill = self.buckets[bucket_key]

            time_passed = current_time - last_refill
            tokens += time_passed * self.refill_rate
            tokens = min(tokens, self.max_tokens_per_minute)

            if tokens >= tokens_required:
                tokens -= tokens_required
                self.buckets[bucket_key] = (tokens, current_time)
                return True, {"remaining": int(tokens), "limit": self.max_tokens_per_minute}
            else:
                self.buckets[bucket_key] = (tokens, current_time)
                reset_in = (tokens_required - tokens) / self.refill_rate
                return False, {
                    "remaining": 0,
                    "limit": self.max_tokens_per_minute,
                    "retry_after": int(reset_in) + 1,
                }


def rate_limit(
    max_requests_per_minute: int = 10,
    tokens_per_request: int = 1,
    endpoint_name: str = None,
):
    """Decorator to rate limit an endpoint."""

    def decorator(f):
        limiter = RateLimiter()
        limiter.set_limits(max_requests_per_minute)

        @wraps(f)
        def decorated_function(*args, **kwargs):
            user_id = (
                getattr(g, "user", None).user_id
                if hasattr(g, "user") and g.user
                else request.remote_addr
            )
            endpoint = endpoint_name or f.__name__

            allowed, status = limiter.is_allowed(
                user_id, endpoint, tokens_per_request
            )

            if not allowed:
                response = jsonify(
                    {
                        "error": "rate_limit_exceeded",
                        "retry_after": status["retry_after"],
                    }
                )
                response.status_code = 429
                response.headers["Retry-After"] = str(status["retry_after"])
                return response

            g.rate_limit_status = status
            return f(*args, **kwargs)

        return decorated_function

    return decorator


def get_rate_limit_status() -> Dict:
    """Get rate limit status for current request."""
    return getattr(g, "rate_limit_status", {})
