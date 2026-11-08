from fastapi import Header, HTTPException, status

from app.models.user import AuthenticatedUser
from app.services.firebase_service import verify_firebase_token


async def get_current_user(authorization: str = Header(...)) -> AuthenticatedUser:
    """
    FastAPI dependency — extracts and verifies Firebase ID token from
    the Authorization header (Bearer <token>).
    Raises 401 if token is missing, malformed, or invalid.
    """
    if not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authorization header must start with 'Bearer '",
        )

    token = authorization.removeprefix("Bearer ").strip()

    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token is missing",
        )

    user = await verify_firebase_token(token)
    return user
