import pytest
from jose import jwt

from app.config import Settings, get_settings
from app.repository import _safe_ident
from app.security import extract_roles


def test_safe_ident_rejects_injection():
    with pytest.raises(ValueError):
        _safe_ident("invoices; drop table invoices")


def test_safe_ident_allows_simple_names():
    assert _safe_ident("invoice_type") == "invoice_type"


def test_extract_roles_from_list():
    settings = Settings()
    roles = extract_roles({"roles": ["role_auditor", "user"]}, settings)
    assert "ROLE_AUDITOR" in roles


def test_extract_roles_from_string():
    settings = Settings()
    roles = extract_roles({"role": "ROLE_AUDITOR"}, settings)
    assert roles == {"ROLE_AUDITOR"}


def test_get_settings_reads_defaults():
    get_settings.cache_clear()
    settings = get_settings()
    assert settings.port == 5000
    get_settings.cache_clear()


def test_jwt_roundtrip():
    settings = Settings(jwt_secret="abc")
    token = jwt.encode({"role": "ROLE_AUDITOR"}, settings.jwt_secret, algorithm=settings.jwt_algorithm)
    payload = jwt.decode(token, settings.jwt_secret, algorithms=[settings.jwt_algorithm])
    assert payload["role"] == "ROLE_AUDITOR"
