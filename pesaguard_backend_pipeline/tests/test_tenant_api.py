import json
import os
import tempfile

import pytest

from pesaguard_backend_pipeline import app as flask_app


@pytest.fixture
def client(monkeypatch):
    # Use a temporary tenant settings file for test isolation
    fd, path = tempfile.mkstemp(prefix='tenant_test_', suffix='.json')
    os.close(fd)
    monkeypatch.setenv('TENANT_SETTINGS_FILE', path)
    monkeypatch.setenv('PESAGUARD_ADMIN_API_TOKEN', 'test-token')

    flask_app.app.config['TESTING'] = True
    with flask_app.app.test_client() as c:
        yield c


def test_admin_get_update_tenant(client):
    # Update tenant via admin POST
    resp = client.post('/admin/tenant/default', headers={'X-Admin-Token': 'test-token'}, json={'preferred_locale': 'sw'})
    assert resp.status_code == 200
    data = resp.get_json()
    assert data.get('preferred_locale') == 'sw'

    # Read back via admin GET
    resp = client.get('/admin/tenant/default', headers={'X-Admin-Token': 'test-token'})
    assert resp.status_code == 200
    data = resp.get_json()
    assert data.get('preferred_locale') == 'sw'


def test_public_tenant_current_exposes_limited_fields(client):
    # Set via admin first
    client.post('/admin/tenant/default', headers={'X-Admin-Token': 'test-token'}, json={'preferred_locale': 'en', 'deployment_region': 'ke-1'})

    resp = client.get('/tenant/current')
    assert resp.status_code == 200
    data = resp.get_json()
    assert 'preferred_locale' in data
    assert 'deployment_region' in data


def test_public_locale_endpoint_persists_preference(client):
    resp = client.post('/tenant/current/locale', json={'preferred_locale': 'sw'})
    assert resp.status_code == 200

    public_resp = client.get('/tenant/current')
    assert public_resp.status_code == 200
    assert public_resp.get_json().get('preferred_locale') == 'sw'
