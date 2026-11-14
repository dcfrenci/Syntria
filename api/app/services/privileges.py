from fastapi import HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Role, User

ROLE_RANK = {
    "admin": 0,
    "manager": 1,
    "secretary": 2,
    "doctor": 2,
    "assistant": 2,
    "employee": 3,
    "client": 4,
}


def _rank(role_name: str) -> int:
    return ROLE_RANK.get(role_name.lower(), 99)


def _is_admin(u: User) -> bool:
    return u.role.name.lower() == "admin"


async def _active_admin_count(db: AsyncSession) -> int:
    q = (
        select(func.count(User.id))
        .join(User.role)
        .where(func.lower(Role.name) == "admin", User.is_active.is_(True))
    )
    return (await db.execute(q)).scalar_one()


async def _guard(
    db: AsyncSession,
    actor: User,
    *,
    target: User | None = None,
    new_role_id: int | None = None,
) -> None:
    """Only an admin may touch an admin account or hand out the Admin role."""
    if _is_admin(actor):
        return
    me = _rank(actor.role.name)
    if target is not None and target.id != actor.id and _rank(target.role.name) <= me:
        raise HTTPException(
            status.HTTP_403_FORBIDDEN,
            detail="You can only modify accounts with a lower role than yours.",
        )
    if new_role_id is not None:
        role = await db.get(Role, new_role_id)
        if role and _rank(role.name) <= me:
            raise HTTPException(
                status.HTTP_403_FORBIDDEN,
                detail="You can only assign roles lower than your own.",
            )
