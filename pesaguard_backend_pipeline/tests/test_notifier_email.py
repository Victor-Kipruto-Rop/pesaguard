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
