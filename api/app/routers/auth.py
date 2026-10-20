import logging
import time
from collections import defaultdict, deque
from typing import Annotated, List
import asyncio
import hashlib
import jwt

from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload, joinedload


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
MAX_FAILS_PER_EMAIL = 50
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


def _check_throttle(key: str, limit: int = MAX_FAILS) -> None:
    now = time.monotonic()
    q = _prune(key, now)
    if q is not None and len(q) >= limit:
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
        while len(_fails) >= MAX_TRACKED:   # evict oldest only
            _fails.pop(next(iter(_fails)))
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

    query = select(User).where(User.id == user_id).options(joinedload(User.person), joinedload(User.role))
    user = (await db.execute(query)).scalar_one_or_none()

    if user is None:
        raise credentials_exception
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Inactive user"
        )
    if user.updated_at is not None and payload.get("iat", 0) < int(user.updated_at.timestamp()):
        raise credentials_exception

    request.state.user_id = user.id
    return user


@router.post("/token", response_model=Token, status_code=status.HTTP_200_OK)
async def login_for_access_token(
    request: Request,
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
    db: AsyncSession = Depends(get_db),
):
    email_key = form_data.username.strip().lower()[:255]
    ip = (request.headers.get("x-real-ip") or (request.client.host if request.client else "unknown"))[:64]
    email_hash = hashlib.sha256(email_key.encode()).hexdigest()[:12]
    pair_key = f"{ip}|{email_key}"
    try:
        _check_throttle(pair_key)
        _check_throttle(email_key, MAX_FAILS_PER_EMAIL)
    except HTTPException:
        log.warning("login throttled ip=%s email_sha=%s", ip, email_hash)
        raise

    query = (
        select(User)
        .join(User.person)
        .where(func.lower(Person.email) == email_key)
        .options(selectinload(User.person), selectinload(User.role))
    )
    user = (await db.execute(query)).scalar_one_or_none()

    # Always run bcrypt, even for unknown emails, so timing doesn't reveal which emails exist
    password_ok = await asyncio.to_thread(
        verify_password,
        form_data.password,
        user.hashed_password if user else _DUMMY_HASH,
    )
    if not user or not password_ok:
        _record_failure(pair_key)
        _record_failure(email_key)
        log.warning("failed login ip=%s email_sha=%s", ip, email_hash)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="User account is deactivated"
        )

    _fails.pop(pair_key, None)
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
