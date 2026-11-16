from datetime import datetime, timedelta, timezone
from sqlalchemy import delete
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.audit import AuditLog
from app.models.users import User


async def audit(
    db: AsyncSession,
    user: User | None,
    action: str,
    entity: str,
    entity_id: int | None = None,
) -> None:
    """Writes an audit trail record for access or mutation of clinical and financial records."""
    log_entry = AuditLog(
        user_id=user.id if user else None,
        action=action,
        entity=entity,
        entity_id=entity_id,
    )
    db.add(log_entry)
    await db.flush()


async def purge_old_audit_logs(db: AsyncSession, keep_days: int = 365) -> int:
    """Deletes audit records older than the retention threshold."""
    cutoff = datetime.now(timezone.utc) - timedelta(days=keep_days)
    result = await db.execute(delete(AuditLog).where(AuditLog.created_at < cutoff))
    await db.flush()
    return result.rowcount