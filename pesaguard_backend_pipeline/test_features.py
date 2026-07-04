"""Integration tests for new PesaGuard features."""

import pytest
from datetime import datetime, timezone, timedelta
from app_2 import app
from models import Base, Discrepancy
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker


@pytest.fixture
def test_client():
    """Create test client with in-memory database."""
    DATABASE_URL = "sqlite:///:memory:"
    engine = create_engine(DATABASE_URL)
    Base.metadata.create_all(engine)
    
    SessionLocal = sessionmaker(bind=engine)
    session = SessionLocal()
    
    # Add test data
    now = datetime.now(timezone.utc)
    
    test_incidents = [
        Discrepancy(
            id="test-1", trans_id="txn-001", anomaly_type="duplicate",
            severity="critical", status="needs_review", resolved=False,
            detected_at=now - timedelta(minutes=50),
        ),
        Discrepancy(
            id="test-2", trans_id="txn-002", anomaly_type="amount_mismatch",
            severity="warning", status="assigned", resolved=False,
            detected_at=now - timedelta(minutes=20),
        ),
        Discrepancy(
            id="test-3", trans_id="txn-003", anomaly_type="missing_transaction",
            severity="critical", status="assigned", resolved=True,
            detected_at=now - timedelta(hours=2),
            resolved_at=now - timedelta(hours=1),
        ),
    ]
    
    for incident in test_incidents:
        session.add(incident)
    session.commit()
    
    with app.test_client() as client:
        yield client
    
    session.close()


def test_reconciliation_report(test_client):
    """Test reconciliation report generation."""
    response = test_client.get('/analytics/reconciliation-report?days=1')
    assert response.status_code == 200
    data = response.get_json()
    
    assert 'summary' in data
    assert data['summary']['total_incidents'] == 3
    assert data['summary']['resolved'] == 1
    assert data['summary']['open'] == 2


def test_incident_trends(test_client):
    """Test incident trends endpoint."""
    response = test_client.get('/analytics/incident-trends')
    assert response.status_code == 200
    data = response.get_json()
    
    assert 'weekly' in data
    assert 'monthly' in data
    assert len(data['weekly']) == 4
    assert len(data['monthly']) == 12


def test_filter_presets_get(test_client):
    """Test retrieving filter presets."""
    response = test_client.get('/incidents/filters/presets')
    assert response.status_code == 200
    data = response.get_json()
    
    assert 'presets' in data
    assert 'critical_open' in data['presets']


def test_filter_presets_post(test_client):
    """Test saving new filter preset."""
    response = test_client.post(
        '/incidents/filters/presets',
        json={'name': 'test_preset', 'filters': {'severity': 'warning'}}
    )
    assert response.status_code == 201
    data = response.get_json()
    
    assert 'presets' in data
    assert 'test_preset' in data['presets']


def test_auto_escalate(test_client):
    """Test auto-escalation of critical incidents."""
    response = test_client.post('/incidents/auto-escalate?escalation_minutes=40')
    assert response.status_code == 200
    data = response.get_json()
    
    assert data['status'] == 'escalated'
    assert data['threshold_minutes'] == 40
    # Should escalate the test-1 incident (50 minutes old, unassigned)
    assert data['count'] >= 1


def test_bulk_assign(test_client):
    """Test bulk assignment of incidents."""
    response = test_client.post(
        '/incidents/bulk-assign',
        json={'ids': ['test-1', 'test-2'], 'assignee': 'john_doe', 'note': 'Test assignment'}
    )
    assert response.status_code == 200
    data = response.get_json()
    
    assert data['status'] == 'assigned'
    assert data['updated'] == 2


def test_search_incidents(test_client):
    """Test full-text search."""
    response = test_client.get('/incidents/search?q=duplicate&page=1&per_page=10')
    assert response.status_code == 200
    data = response.get_json()
    
    assert 'items' in data
    assert data['query'] == 'duplicate'


def test_search_with_filters(test_client):
    """Test search with severity and assignee filters."""
    response = test_client.get('/incidents/search?severity=critical&page=1')
    assert response.status_code == 200
    data = response.get_json()
    
    assert data['total'] >= 1


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
