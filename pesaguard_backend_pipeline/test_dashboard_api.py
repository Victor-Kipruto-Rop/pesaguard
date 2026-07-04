import importlib
import os
import tempfile

import pytest


@pytest.fixture()
def dashboard_app(monkeypatch):
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = os.path.join(tmpdir, "pesaguard_test.db")
        monkeypatch.setenv("DATABASE_URL", f"sqlite:///{db_path}")
        import app_2

        app_2 = importlib.reload(app_2)
        app_2.Base.metadata.create_all(app_2.engine)
        app_2.app.config.update(TESTING=True)

        session = app_2.SessionLocal()
        try:
            session.add_all([
                app_2.Discrepancy(
                    id="tx-1-missing",
                    trans_id="tx-1",
                    tenant_id="tenant-a",
                    anomaly_type="missing_payment",
                    status="needs_review",
                    severity="critical",
                    details="Initial mismatch",
                    resolved=False,
                ),
                app_2.Discrepancy(
                    id="tx-2-duplicate",
                    trans_id="tx-2",
                    tenant_id="tenant-b",
                    anomaly_type="duplicate",
                    status="needs_review",
                    severity="warning",
                    details="Duplicate callback detected",
                    resolved=False,
                ),
                app_2.Discrepancy(
                    id="tx-3-review",
                    trans_id="tx-3",
                    tenant_id="tenant-a",
                    anomaly_type="needs_review",
                    status="needs_review",
                    severity="info",
                    details="Pending manual review",
                    resolved=False,
                ),
            ])
            session.commit()
        finally:
            session.close()

        with app_2.app.test_client() as client:
            yield client, app_2


def test_dashboard_filters_and_resolves_discrepancies(dashboard_app):
    client, app_module = dashboard_app

    response = client.get("/discrepancies?status=missing_payment")
    assert response.status_code == 200
    payload = response.get_json()
    assert len(payload["items"]) == 1
    assert payload["items"][0]["anomaly_type"] == "missing_payment"

    resolve_response = client.post(
        f"/discrepancies/{payload['items'][0]['id']}/resolve",
        json={"note": "Manual investigation complete"},
    )
    assert resolve_response.status_code == 200

    session = app_module.SessionLocal()
    try:
        discrepancy = session.get(app_module.Discrepancy, payload["items"][0]["id"])
        assert discrepancy.resolved is True
        assert discrepancy.resolution_note == "Manual investigation complete"
    finally:
        session.close()


def test_dashboard_supports_pagination_and_bulk_resolve(dashboard_app):
    client, app_module = dashboard_app

    paged_response = client.get("/discrepancies?page=1&per_page=2")
    assert paged_response.status_code == 200
    paged_payload = paged_response.get_json()
    assert paged_payload["page"] == 1
    assert paged_payload["per_page"] == 2
    assert len(paged_payload["items"]) == 2
    assert paged_payload["total"] == 3

    bulk_response = client.post(
        "/discrepancies/bulk-resolve",
        json={"ids": [item["id"] for item in paged_payload["items"]], "note": "Bulk resolved"},
    )
    assert bulk_response.status_code == 200
    assert bulk_response.get_json()["updated"] == 2

    session = app_module.SessionLocal()
    try:
        resolved_items = session.query(app_module.Discrepancy).filter(app_module.Discrepancy.resolved.is_(True)).all()
        assert len(resolved_items) == 2
        assert all(item.resolution_note == "Bulk resolved" for item in resolved_items)
    finally:
        session.close()
