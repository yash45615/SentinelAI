from app.core.security import require_admin_api_key


def test_security_module_exists():
    assert require_admin_api_key is not None


def test_security_disabled_allows_development():
    from app.core.config import settings

    original = settings.security_enabled

    try:
        settings.security_enabled = False

        result = require_admin_api_key(None)

        assert result == "development"

    finally:
        settings.security_enabled = original


def test_security_requires_key_when_enabled():
    from fastapi import HTTPException

    from app.core.config import settings

    original = settings.security_enabled

    try:
        settings.security_enabled = True

        try:
            require_admin_api_key(None)
            assert False, "Expected HTTPException"
        except HTTPException as exc:
            assert exc.status_code == 401

    finally:
        settings.security_enabled = original


def test_security_rejects_invalid_key():
    from fastapi import HTTPException

    from app.core.config import settings

    original_enabled = settings.security_enabled
    original_key = settings.admin_api_key

    try:
        settings.security_enabled = True
        settings.admin_api_key = "correct-key"

        try:
            require_admin_api_key("wrong-key")
            assert False, "Expected HTTPException"
        except HTTPException as exc:
            assert exc.status_code == 403

    finally:
        settings.security_enabled = original_enabled
        settings.admin_api_key = original_key


def test_security_accepts_valid_key():
    from app.core.config import settings

    original_enabled = settings.security_enabled
    original_key = settings.admin_api_key

    try:
        settings.security_enabled = True
        settings.admin_api_key = "correct-key"

        result = require_admin_api_key("correct-key")

        assert result == "admin"

    finally:
        settings.security_enabled = original_enabled
        settings.admin_api_key = original_key