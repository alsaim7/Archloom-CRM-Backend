from datetime import timedelta
from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session, select

from database import get_session
from models import User
from schemas.user_schema import LoginSchema, Token
from security.token_jwt import create_access_token, ACCESS_TOKEN_EXPIRE_MINUTES
from security.hashing import verify_password


router = APIRouter(tags=["Auth"])



@router.post("/login", response_model=Token, status_code=status.HTTP_202_ACCEPTED)
def login(req: LoginSchema, db: Session = Depends(get_session)):
    user = db.exec(select(User).where(User.email == req.email)).first()
    if not user:
        raise HTTPException(status_code=404, detail="Incorrect email or password")
    if not verify_password(req.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Incorrect email or password")
    expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    token = create_access_token(
    data={"sub": user.email, "user_id": user.id, "name": user.name},
    expires_delta=expires
)
    return Token(access_token=token)
