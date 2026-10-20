from decimal import Decimal

import pytest
from fastapi import HTTPException
from pydantic import ValidationError

from app.core.security import get_password_hash, verify_password
from app.routers import auth
from app.routers.import_export import _clean_row, _csv_safe, _csv_unsafe, _parse_csv
from app.schemas.presets import ComponentSchema
from app.schemas.quotes import QuoteItemCreate


def _img(content):
    return ComponentSchema(id="a", type="image", x=0, y=0, w=1, h=1, content=content)


def test_csv_formula_guard_roundtrips():
    for v in ["=SUM(A1)", "+1", "-1", "@x", "plain"]:
        assert _csv_unsafe(_csv_safe(v)) == v
    assert _csv_safe("=1+1").startswith("'")


def test_parse_csv_empty_cells_prefix_and_row_limit():
    assert _parse_csv(b"id,name\n1,\n2,x\n") == [
        {"id": "1", "name": None},
        {"id": "2", "name": "x"},
    ]
    assert _parse_csv(b"id,name\n1,'=cmd\n")[0]["name"] == "=cmd"
    with pytest.raises(ValueError):
        _parse_csv(b"id\n" + b"1\n" * 5001)


def test_quote_total_is_recomputed_not_trusted():
    row = _clean_row(
        "quotes",
        {
            "status": "Draft",
            "total_amount": "999999",
            "items": [{"item_id": 1, "quantity": 2, "unit_price": "10.00", "discount": "5"}],
        },
    )
    assert row["total_amount"] == Decimal("15.00")


@pytest.mark.parametrize("price", ["-1", "0", "1.234", "abc"])
def test_item_import_rejects_bad_price(price):
    with pytest.raises(HTTPException) as e:
        _clean_row("items", {"name": "Valid name", "price": price})
    assert e.value.status_code == 422


def test_item_import_coerces_csv_booleans():
    row = _clean_row(
        "items", {"name": "Valid", "price": "80.0", "is_active": "False", "is_specific": "True"}
    )
    assert row["is_active"] is False and row["is_specific"] is True


def test_reservation_import_requires_staff():
    base = {"reservation_date": "2026-10-02T10:00:00Z", "duration_minutes": "30"}
    with pytest.raises(HTTPException):
        _clean_row("reservations", {**base, "staff": []})
    assert _clean_row("reservations", {**base, "staff": [{"id": 1}]})["duration_minutes"] == 30


@pytest.mark.parametrize(
    "bad", ["data:image/svg+xml;base64,AAAA", "http://evil/x.png", 'x" onerror="y']
)
def test_image_component_rejects_svg_urls_and_attribute_breakouts(bad):
    with pytest.raises(ValidationError):
        _img(bad)


def test_image_component_accepts_reference():
    assert _img("image:12").content == "image:12"


def test_teeth_range_enforced():
    with pytest.raises(ValidationError):
        QuoteItemCreate(item_id=1, teeth=[99])


def test_password_hashing_and_garbage_hash():
    h = get_password_hash("correct horse battery")
    assert verify_password("correct horse battery", h)
    assert not verify_password("wrong", h)
    assert verify_password("x", "not-a-hash") is False
    with pytest.raises(ValueError):
        get_password_hash("é" * 37)  # 74 bytes > bcrypt limit


def test_login_throttle_locks_after_max_fails():
    auth._fails.clear()
    for _ in range(auth.MAX_FAILS):
        auth._record_failure("k")
    with pytest.raises(HTTPException) as e:
        auth._check_throttle("k")
    assert e.value.status_code == 429