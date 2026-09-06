import importlib
import os

os.environ.setdefault('JWT_SECRET_KEY', 'test-secret-key-for-identity-policy-hardening')

mod = importlib.import_module('pesaguard_backend_pipeline.app_4_advanced_features')


def test_provider_trust_policy_rejects_untrusted_issuer_for_tenant():
    policy = mod._provider_trust_policy_for_tenant('tenant-a')
    assert policy['provider_type'] in {'oidc', 'saml'}

    bad = mod._validate_provider_trust_policy(
        'tenant-a',
        {
            'provider_type': 'oidc',
            'issuer': 'https://evil.example.com',
            'jwks_uri': 'https://evil.example.com/jwks',
            'allowed_issuers': ['https://login.microsoftonline.com/tenant-a/v2.0'],
        },
        {
            'issuer': 'https://evil.example.com',
            'jwks_uri': 'https://evil.example.com/jwks',
        },
    )

    assert bad is False


def test_session_risk_flags_new_device_and_geo_mismatch():
    risk = mod._evaluate_session_risk(
        tenant_id='tenant-a',
        user_id='user-1',
        ip_address='203.0.113.99',
        user_agent='curl/8.0',
        device_id='new-device',
        known_devices=['device-old'],
        country='KE',
        known_country='US',
    )

    assert risk['risk_score'] >= 0.5
    assert risk['requires_reauth'] is True
    assert risk['signals']['new_device'] is True


def test_provider_family_defaults_apply_tenant_specific_patterns(monkeypatch):
    monkeypatch.setenv('OIDC_PROVIDER_FAMILY', 'microsoft_entra')
    monkeypatch.setenv('TENANT_ID', 'tenant-a')
    monkeypatch.delenv('OIDC_ALLOWED_ISSUERS', raising=False)
    monkeypatch.delenv('OIDC_ALLOWED_JWKS_HOSTS', raising=False)

    policy = mod._provider_trust_policy_for_tenant('tenant-a')

    assert 'https://login.microsoftonline.com/tenant-a/v2.0' in policy['allowed_issuers']
    assert 'login.microsoftonline.com' in policy['allowed_jwks_hosts']


def test_admin_review_gate_and_redis_fail_closed_defaults(monkeypatch):
    monkeypatch.setenv('REDIS_URL', 'redis://redis.internal:6379/0')
    monkeypatch.setenv('PESAGUARD_FAIL_CLOSED_REDIS', '1')
    config = mod._redis_fail_closed_config()
    assert config['fail_closed'] is True
    assert config['url'].startswith('redis://')

    review_policy = {'provider_type': 'oidc', 'review_required': True, 'approved_by': ''}
    assert mod._validate_provider_trust_policy('tenant-a', review_policy, {'issuer': 'https://login.microsoftonline.com/tenant-a/v2.0'}) is False


def test_saml_policy_requires_explicit_entity_id():
    ok = mod._validate_saml_provider_policy(
        {'provider_type': 'saml', 'entity_id': 'https://idp.example.com/saml'}
    )
    bad = mod._validate_saml_provider_policy({'provider_type': 'saml'})

    assert ok is True
    assert bad is False
