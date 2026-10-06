from fastapi import Header, HTTPException, status

from app.core.config import settings


def require_admin_api_key(
    x_admin_api_key: str | None = Header(default=None),
) -> str:
    """
    Protect sensitive SentinelAI operations.

    Security enforcement is enabled only when SECURITY_ENABLED=true.
    This keeps local development convenient while allowing production
    deployments to require an API key.
    """

    if not settings.security_enabled:
        return "development"

    if not x_admin_api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Admin API key required.",
        )

    if x_admin_api_key != settings.admin_api_key:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid admin API key.",
        )

    return "admin"