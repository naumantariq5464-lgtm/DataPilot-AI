from pydantic import BaseModel


class AuthenticatedUser(BaseModel):
    """Decoded Firebase JWT payload — attached to every protected request."""

    uid: str
    email: str | None = None
    name: str | None = None
