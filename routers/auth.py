from datetime import timedelta
from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session, select

from database import get_session
from models import User
from schemas.user_schema import LoginSchema, Token, UserReadSchema  # Make sure UserReadSchema is imported
from security.token_jwt import create_access_token, ACCESS_TOKEN_EXPIRE_MINUTES
from security.oauth2 import get_current_user  # Import this
from security.hashing import verify_password

router = APIRouter(tags=["Auth"])

@router.post("/login", response_model=Token, status_code=status.HTTP_202_ACCEPTED)
def login(req: LoginSchema, db: Session = Depends(get_session)):
    user = db.exec(select(User).where(User.email == req.email)).first()
    if not user:
        raise HTTPException(status_code=404, detail="Incorrect email or password")
    if not verify_password(req.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Incorrect email or password")
    
    # 🚫 Check if the user is deactivated
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Login failed. Please contact admin."
        )
    
    expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    token = create_access_token(
        data={
            "sub": user.email, 
            "user_id": user.id, 
            "name": user.name
            },
        expires_delta=expires
    )
    return Token(access_token=token)

# ✅ ADD THIS ENDPOINT
@router.get("/me", response_model=UserReadSchema)
async def get_current_user_info(
    current_user: User = Depends(get_current_user)
):
    """Get current user information"""
    return current_user