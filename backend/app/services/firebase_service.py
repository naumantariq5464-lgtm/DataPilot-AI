import firebase_admin
from firebase_admin import credentials, auth
from fastapi import HTTPException, status
from pathlib import Path

from app.config import settings
from app.models.user import AuthenticatedUser

# ── Firebase app initialization (lazy — only when first token is verified) ───

_firebase_initialized = False


def _init_firebase() -> None:
    """Initialize Firebase Admin SDK if not already done."""
    global _firebase_initialized
    if _firebase_initialized:
        return

    sa_path = Path(settings.firebase_service_account_path)
    if not sa_path.exists():
        raise RuntimeError(
            f"Firebase service account file not found: {sa_path}. "
            "Download it from Firebase Console → Project Settings → Service Accounts."
        )

    try:
        cred = credentials.Certificate(str(sa_path))
        firebase_admin.initialize_app(cred)
        _firebase_initialized = True
        print("[Firebase] Initialized successfully.")
    except Exception as e:
        raise RuntimeError(f"Firebase initialization failed: {e}") from e


# ── Token verification ────────────────────────────────────────────────────────

async def verify_firebase_token(token: str) -> AuthenticatedUser:
    """
    Verifies a Firebase ID token and returns the decoded user.
    Raises HTTP 401 if the token is invalid or expired.
    Initializes Firebase on first call (lazy init).
    """
    try:
        _init_firebase()
    except RuntimeError as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(e),
        )

    try:
        decoded = auth.verify_id_token(token)
        return AuthenticatedUser(
            uid=decoded["uid"],
            email=decoded.get("email"),
            name=decoded.get("name"),
        )
    except auth.ExpiredIdTokenError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has expired. Please log in again.",
        )
    except auth.InvalidIdTokenError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token.",
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Token verification failed: {str(e)}",
        )
