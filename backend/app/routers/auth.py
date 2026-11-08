from fastapi import APIRouter, Depends

from app.dependencies import get_current_user
from app.models.user import AuthenticatedUser

router = APIRouter()


@router.get("/me")
async def get_me(current_user: AuthenticatedUser = Depends(get_current_user)):
    """
    Returns the authenticated user's profile.
    Useful for the frontend to verify the token is valid.
    """
    return {
        "uid": current_user.uid,
        "email": current_user.email,
        "name": current_user.name,
    }
