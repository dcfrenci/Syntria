from pydantic import BaseModel, EmailStr


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


class TokenPayload(BaseModel):
    sub: str | None = None  # Holds the User ID as string
    email: EmailStr | None = None
    role: str | None = None


class LoginRequest(BaseModel):
    """Used for JSON-based login bodies (alternative to OAuth2 form)."""
    email: EmailStr
    password: str