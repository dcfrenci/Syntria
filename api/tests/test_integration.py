import pytest
from datetime import datetime
from fastapi import HTTPException
from sqlalchemy.exc import SQLAlchemyError

from app.core.security import _guard, _can_access
from app.core.database import _do_commit
from app.routers.scheduling import find_conflict
from app.schemas.users import UserUpdate


@pytest.mark.asyncio
async def test_find_conflict_detects_overlap(db_session, seeded):
    """Ensures the scheduling engine properly identifies overlapping appointments."""
    start = datetime(2026, 10, 2, 10, 0)
    patient_id = 1
    doc_id = 2
    
    msg = await find_conflict(db_session, start, 30, patient_id, [doc_id])
    assert msg and "conflict" in msg


def test_guard_enforces_role_authorization():
    """Verifies that route authorization guards reject unauthorized roles."""
    user = {"sub": "1", "role": "patient"}
    with pytest.raises(HTTPException) as exc:
        _guard(user, allowed_roles=["admin", "staff"])
    assert exc.value.status_code == 403


def test_can_access_blocks_idor_issue_05_regression():
    """ISSUE-05 Regression: Users must not be able to access other users' private data (IDOR)."""
    user = {"sub": "1", "role": "patient"}
    
    # Allowed: Accessing their own data
    assert _can_access(user, resource_owner_id=1) is True
    
    # Denied: Accessing another user's data
    assert _can_access(user, resource_owner_id=2) is False
    
    # Allowed: Admins can access any user's data
    admin = {"sub": "99", "role": "admin"}
    assert _can_access(admin, resource_owner_id=2) is True


@pytest.mark.asyncio
async def test_do_commit_rolls_back_on_error(mocker):
    """Verifies that a failing database commit forces a safe rollback."""
    db_session = mocker.Mock()
    db_session.commit.side_effect = SQLAlchemyError("Simulated DB commit failure")
    
    with pytest.raises(HTTPException) as exc:
        await _do_commit(db_session)
        
    assert exc.value.status_code == 400
    db_session.rollback.assert_called_once()


def test_mass_assignment_and_escalation_issue_01_04_regression():
    """ISSUE-01 & ISSUE-04 Regression: Privilege escalation and mass assignment via schema over-posting."""
    payload = {
        "name": "Hacked Name", 
        "role": "admin",  # Escalation attempt
        "id": 999         # Mass assignment attempt
    }
    
    update_schema = UserUpdate(**payload)
    dump = update_schema.model_dump(exclude_unset=True)
    
    assert "role" not in dump, "Role escalation via over-posting must be stripped by the schema"
    assert "id" not in dump, "Mass assignment of record IDs must be stripped by the schema"
    assert dump.get("name") == "Hacked Name"