from sqlalchemy.orm import Session

from app.models.audit_log import AuditLog


def record_audit(
    db: Session,
    *,
    actor: str,
    action: str,
    resource_type: str,
    resource_id: str | None,
    outcome: str,
    details: str,
    request_id: str | None = None,
) -> AuditLog:
    audit = AuditLog(
        request_id=request_id,
        actor=actor,
        action=action,
        resource_type=resource_type,
        resource_id=resource_id,
        outcome=outcome,
        details=details,
    )

    db.add(audit)
    db.flush()

    return audit