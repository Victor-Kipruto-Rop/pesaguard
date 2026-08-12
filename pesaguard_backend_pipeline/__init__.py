"""PesaGuard backend package compatibility layer."""

import importlib
import os
import sys

PACKAGE_ROOT = os.path.dirname(__file__)
if PACKAGE_ROOT not in sys.path:
    sys.path.insert(0, PACKAGE_ROOT)

# Provide stable top-level module aliases so the package and the legacy
# top-level imports resolve to the same module objects during tests and local runs.
for module_name in [
    "action_audit",
    "auth_rbac",
    "event_store",
    "export_routes",
    "health",
    "init_db",
    "logging_utils",
    "models",
    "producer",
    "rate_limiter",
    "security_helpers",
    "tenant_settings",
    "validators",
]:
    try:
        module = importlib.import_module(f"pesaguard_backend_pipeline.{module_name}")
    except ImportError:
        continue
    sys.modules.setdefault(module_name, module)
