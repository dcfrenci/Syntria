import logging
import time
from collections import defaultdict, deque
from typing import Annotated, List

import jwt
from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.config import settings
from app.core.database import get_db
from app.core.security import create_access_token, get_password_hash, verify_password
from app.models import User
from app.models.persons import Person
from app.schemas.auth import Token

log = logging.getLogger("syntria.auth")
router = APIRouter(prefix="/auth", tags=["Authentication"])
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/token")

# --- Per-account brute-force protection (in-memory: valid because uvicorn runs ONE worker) ---
_DUMMY_HASH = get_password_hash("dummy-password-0")
MAX_FAILS = 5
WINDOW_SECONDS = 15 * 60
MAX_TRACKED = 10_000
_fails: dict[str, deque[float]] = defaultdict(deque)


def _prune(key: str, now: float) -> deque[float] | None:
    q = _fails.get(key)
    if q is None:
        return None
    while q and now - q[0] > WINDOW_SECONDS:
        q.popleft()
    if not q:
        _fails.pop(key, None)
        return None
    return q


def _check_throttle(key: str) -> None:
    now = time.monotonic()
    q = _prune(key, now)
    if q is not None and len(q) >= MAX_FAILS:
        retry = int(WINDOW_SECONDS - (now - q[0])) + 1
        raise HTTPException(
            status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Too many failed attempts. Try again later.",
            headers={"Retry-After": str(retry)},
        )


def _record_failure(key: str) -> None:
    now = time.monotonic()
    if len(_fails) >= MAX_TRACKED:
        for k in list(_fails):
            _prune(k, now)
        if len(_fails) >= MAX_TRACKED:
            _fails.clear()
    _fails[key].append(now)


# --- Protected Route Dependency ---
async def get_current_user(
    request: Request,
    token: Annotated[str, Depends(oauth2_scheme)],
    db: AsyncSession = Depends(get_db),
) -> User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(
            token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM]
        )
        user_id = int(payload.get("sub"))
    except (jwt.PyJWTError, TypeError, ValueError):
        raise credentials_exception

    query = (
        select(User)
        .where(User.id == user_id)
        .options(selectinload(User.person), selectinload(User.role))
    )
    user = (await db.execute(query)).scalar_one_or_none()

    if user is None:
        raise credentials_exception
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Inactive user"
        )

    request.state.user_id = user.id
    return user


@router.post("/token", response_model=Token, status_code=status.HTTP_200_OK)
async def login_for_access_token(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
    db: AsyncSession = Depends(get_db),
):
    key = form_data.username.strip().lower()[:255]
    _check_throttle(key)

    query = (
        select(User)
        .join(User.person)
        .where(Person.email == form_data.username)
        .options(selectinload(User.person), selectinload(User.role))
    )
    user = (await db.execute(query)).scalar_one_or_none()

    # Always run bcrypt, even for unknown emails, so timing doesn't reveal which emails exist
    password_ok = verify_password(
        form_data.password, user.hashed_password if user else _DUMMY_HASH
    )
    if not user or not password_ok:
        _record_failure(key)
        log.warning("failed login attempt")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="User account is deactivated"
        )

    _fails.pop(key, None)
    token_data = {
        "sub": str(user.id),
        "email": user.person.email,
        "role": user.role.name,
        "first_name": user.person.first_name,
        "last_name": user.person.last_name,
    }
    return {
        "access_token": create_access_token(data=token_data),
        "token_type": "bearer",
    }


class RoleChecker:
    def __init__(self, allowed_roles: List[str]):
        self.allowed_roles = [r.lower() for r in allowed_roles]

    async def __call__(self, current_user: User = Depends(get_current_user)) -> User:
        if current_user.role.name.lower() not in self.allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Operation not permitted. Insufficient privileges.",
            )
        return current_user
