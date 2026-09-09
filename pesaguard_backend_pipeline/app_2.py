"""Compatibility import for the canonical dashboard API.

The implementation lives in :mod:`pesaguard_backend_pipeline.api.dashboard_app`.
This module remains so existing tests, WSGI settings, and operator commands keep
the same import path while the package is reorganized.
"""

from __future__ import annotations

import sys

from pesaguard_backend_pipeline.api import dashboard_app as _dashboard_app

sys.modules[__name__] = _dashboard_app
