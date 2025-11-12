from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session, select
from database import get_session
from models import User
from security.oauth2 import get_current_user
from schemas.user_schema import UserReadSchema

router = APIRouter(
    tags=["User"],
    dependencies=[Depends(get_current_user)]
)


# Add this to your registration routes or user routes
@router.get("/users", response_model=list[UserReadSchema], status_code=status.HTTP_200_OK)
def get_users(
    db: Session = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    try:
        # Only admin can see all users
        if current_user.role != "admin":
            raise HTTPException(status_code=403, detail="Not authorized")
        
        users = db.exec(select(User)).all()
        return users
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch users: {str(e)}")