"""Operational CLI. Run inside the api container:

    docker compose exec api python -m app.cli bootstrap
    docker compose exec api python -m app.cli set-password [--email someone@x.it]

Non-interactive (local automation only): pass -e ADMIN_PASSWORD=... to `exec`.
"""
import argparse
import asyncio
import getpass
import os
import sys

from sqlalchemy import select

from app.core.config import settings
from app.core.database import AsyncSessionLocal, Base, engine
from app.core.security import get_password_hash
from app.models import Person, ReminderPreference, Role, User  # noqa: F401 (registers all tables)

ROLES = ["Admin", "Manager", "Secretary", "Doctor", "Assistant", "Employee", "Client"]
REMINDERS = ["Sms", "WhatsApp", "Telegram"]
MIN_PASSWORD_LEN = 12


def read_password() -> str:
    pw = os.environ.get("ADMIN_PASSWORD")
    if not pw:
        if not sys.stdin.isatty():
            sys.exit("No TTY. Use `docker compose exec api ...` interactively, or pass ADMIN_PASSWORD.")
        pw = getpass.getpass("New password: ")
        if pw != getpass.getpass("Repeat password: "):
            sys.exit("Passwords do not match.")
    if len(pw) < MIN_PASSWORD_LEN:
        sys.exit(f"Password must be at least {MIN_PASSWORD_LEN} characters.")
    if len(pw.encode("utf-8")) > 72:
        sys.exit("Password must not exceed 72 bytes (bcrypt limit).")
    return pw


async def seed_reference_data(db) -> None:
    """Idempotent. Admin is created first so it gets role id 1."""
    for name in ROLES:
        if (await db.execute(select(Role).where(Role.name == name))).scalar_one_or_none() is None:
            db.add(Role(name=name))
            await db.flush()
    for name in REMINDERS:
        found = await db.execute(select(ReminderPreference).where(ReminderPreference.name == name))
        if found.scalar_one_or_none() is None:
            db.add(ReminderPreference(name=name))
            await db.flush()


async def bootstrap(args) -> None:
    async with engine.begin() as conn:  # replaced by Alembic in step 2
        await conn.run_sync(Base.metadata.create_all)

    async with AsyncSessionLocal() as db:
        await seed_reference_data(db)
        admin_role = (await db.execute(select(Role).where(Role.name == "Admin"))).scalar_one()

        existing = (
            await db.execute(select(User.id).where(User.role_id == admin_role.id).limit(1))
        ).first()
        if existing:
            await db.commit()  # keep the reference data
            sys.exit("An admin already exists. Use `set-password` to reset its password.")

        password = read_password()
        email = settings.ADMIN_EMAIL
        person = (await db.execute(select(Person).where(Person.email == email))).scalar_one_or_none()
        if person is None:
            person = Person(first_name=args.first_name, last_name=args.last_name, email=email)
            db.add(person)
            await db.flush()

        db.add(
            User(
                person_id=person.id,
                role_id=admin_role.id,
                hashed_password=get_password_hash(password),
                is_active=True,
            )
        )
        await db.commit()
    print(f"Admin '{settings.ADMIN_EMAIL}' created. Roles and reminder preferences seeded.")


async def set_password(args) -> None:
    password = read_password()
    async with AsyncSessionLocal() as db:
        user = (
            await db.execute(select(User).join(User.person).where(Person.email == args.email))
        ).scalar_one_or_none()
        if user is None:
            sys.exit(f"No user with email {args.email}.")
        user.hashed_password = get_password_hash(password)
        user.is_active = True  # also unlocks a deactivated admin
        await db.commit()
    print(f"Password updated for {args.email}.")


def main() -> None:
    parser = argparse.ArgumentParser(prog="python -m app.cli")
    sub = parser.add_subparsers(dest="cmd", required=True)

    b = sub.add_parser("bootstrap", help="seed roles/reminders and create the first admin")
    b.add_argument("--first-name", default="Admin")
    b.add_argument("--last-name", default="System")

    s = sub.add_parser("set-password", help="reset a user's password (default: the admin)")
    s.add_argument("--email", default=settings.ADMIN_EMAIL)

    args = parser.parse_args()

    async def run():
        try:
            await (bootstrap if args.cmd == "bootstrap" else set_password)(args)
        finally:
            await engine.dispose()

    asyncio.run(run())


if __name__ == "__main__":
    main()