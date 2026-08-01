import importlib
import os
import sys
from pathlib import Path

os.environ.setdefault("USE_IN_MEMORY_TEST_DB", "true")
os.environ.setdefault("PESAGUARD_API_AUTH_REQUIRED", "0")

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


def test_unified_app_imports_and_exposes_health_and_metrics():
    os.environ.setdefault("DATABASE_URL", "sqlite:///:memory:")
    os.environ.setdefault("USE_IN_MEMORY_TEST_DB", "true")

    import pesaguard_backend_pipeline.app as app_module
    import pesaguard_backend_pipeline.app_2 as package_app_2

    app_module = importlib.reload(app_module)
    package_app_2 = importlib.reload(package_app_2)
    client = app_module.app.test_client()

    assert package_app_2.app is app_module.app

    health_response = client.get("/health")
    assert health_response.status_code in {200, 503}

    metrics_response = client.get("/metrics")
    assert metrics_response.status_code == 200
