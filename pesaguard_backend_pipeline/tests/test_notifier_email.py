import os
import sys
sys.path.insert(0, 'pesaguard_backend_pipeline')

import notifier
from notifier import send_email_alert, send_sms_alert


class DummySMTP:
    def __init__(self, host, port, timeout=5):
        self.host = host
        self.port = port
        self.sent = []

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False

    def starttls(self):
        pass

    def login(self, user, password):
        pass

    def send_message(self, msg):
        # record the message for assertion
        self.sent.append(msg)


def test_send_email_alert(monkeypatch, tmp_path):
    monkeypatch.setenv('ALERT_EMAIL_RECIPIENTS', 'ops@example.com')
    monkeypatch.setenv('ALERT_SMTP_HOST', 'smtp.example')
    monkeypatch.setenv('ALERT_SMTP_PORT', '25')
    monkeypatch.setenv('ALERT_SMTP_USER', '')
    monkeypatch.setenv('ALERT_SMTP_PASS', '')

    sent = []

    def fake_smtp(host, port, timeout=5):
        return DummySMTP(host, port)

    monkeypatch.setattr('smtplib.SMTP', fake_smtp)

    discrepancy = {'trans_id': 'T123', 'severity': 'critical'}
    # Should not raise
    notifier.send_email_alert(discrepancy, locale='en')


def test_send_sms_alert_uses_swahili_template(monkeypatch):
    monkeypatch.setenv('SMS_ALERT_RECIPIENT', '254700000000')
    captured = {}

    class FakeSMSClient:
        def send_sms(self, recipient, message):
            captured['recipient'] = recipient
            captured['message'] = message

    monkeypatch.setattr(notifier, 'sms_client', FakeSMSClient())

    discrepancy = {'trans_id': 'T123', 'severity': 'critical', 'status': 'needs_review', 'anomalies': ['mismatch']}
    notifier.send_sms_alert(discrepancy, locale='sw')

    assert captured['recipient'] == '254700000000'
    assert 'PesaGuard imegundua tofauti' in captured['message']


def test_format_alert_text_uses_swahili_template_and_kenyan_formatting():
    discrepancy = {
        'trans_id': 'T123',
        'severity': 'critical',
        'status': 'missing_payment',
        'anomalies': ['missing_payment'],
        'checked_at': '2026-07-04T00:00:00Z',
        'amount': 1000.5,
    }

    text = notifier._format_alert_text(discrepancy, locale='sw-KE')
    assert 'PesaGuard imegundua tofauti' in text
    assert 'Muamala' in text
    assert 'Kiasi: KES 1,000.50' in text
    assert 'Iligunduliwa saa' in text


def test_format_alert_text_normalizes_unknown_locale_to_english():
    discrepancy = {
        'trans_id': 'T123',
        'severity': 'critical',
        'status': 'missing_payment',
        'anomalies': ['missing_payment'],
        'checked_at': '2026-07-04T00:00:00Z',
        'amount': 1000.5,
    }

    text = notifier._format_alert_text(discrepancy, locale='EN-US')
    assert 'PesaGuard discrepancy detected' in text
    assert 'Transaction' in text
    assert 'Amount: KES 1,000.50' in text
    assert 'Detected at' in text


def test_alerting_service_resolves_locale_from_tenant_settings(monkeypatch):
    from alerting_service import AlertingService

    service = AlertingService(session=None, tenant_settings={
        'default': {'preferred_locale': 'en'},
        'tenant-a': {
            'preferred_locale': 'sw',
            'user_locale_overrides': {'user-1': 'en'},
        },
    })

    assert service._resolve_locale({'tenant_id': 'tenant-a'}) == 'sw'
    assert service._resolve_locale({'tenant_id': 'tenant-a', 'user_id': 'user-1'}) == 'en'
