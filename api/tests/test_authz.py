from types import SimpleNamespace as NS
from app.routers.quotes import _can_access


def _u(role: str, pid: int) -> NS:
    return NS(role=NS(name=role), person_id=pid)


def _q(patient: int, staff: int) -> NS:
    return NS(patient=NS(email="p@x.it"), patient_id=patient, staff_id=staff)


def test_doctor_sees_only_own_quotes():
    assert _can_access(_q(5, 2), _u("Doctor", 2))
    assert not _can_access(_q(5, 3), _u("Doctor", 2))


def test_client_cannot_read_foreign_quote():
    assert not _can_access(_q(5, 2), _u("Client", 6))