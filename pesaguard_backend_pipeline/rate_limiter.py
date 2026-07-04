"""Rate limiting for bulk operations to prevent abuse."""

import time
from typing import Dict, Tuple
from functools import wraps
from flask import request, jsonify, g
from collections import defaultdict


class RateLimiter:
    """Token bucket rate limiter for API endpoints."""

    def __init__(self):
        # key: (user_id, endpoint), value: (tokens, last_refill_time)
        self.buckets: Dict[str, Tuple[float, float]] = {}
        self.max_tokens_per_minute = 10  # default
        self.refill_rate = 10 / 60  # tokens per second

    def set_limits(self, max_requests_per_minute: int, endpoint: str = None):
        """Set rate limit for an endpoint."""
        self.max_tokens_per_minute = max_requests_per_minute
        self.refill_rate = max_requests_per_minute / 60

    def get_bucket_key(self, user_id: str, endpoint: str) -> str:
        """Generate bucket key from user ID and endpoint."""
        return f"{user_id}:{endpoint}"

    def is_allowed(self, user_id: str, endpoint: str, tokens_required: int = 1) -> Tuple[bool, Dict]:
        """Check if request is within rate limits."""
        bucket_key = self.get_bucket_key(user_id, endpoint)
        current_time = time.time()

        if bucket_key not in self.buckets:
            self.buckets[bucket_key] = (self.max_tokens_per_minute, current_time)

        tokens, last_refill = self.buckets[bucket_key]

        # Refill tokens based on time elapsed
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
