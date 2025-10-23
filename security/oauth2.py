from fastapi import Depends, HTTPException, status
from typing import Annotated
from fastapi.security import OAuth2PasswordBearer
from sqlmodel import Session, select
import jwt

from security.token_jwt import SECRET_KEY, ALGORITHM
from schemas.user_schema import TokenData
from models import User
from database import get_session  # provide your session dependency

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")  # only used for docs; login uses JSON body
    

def get_current_user(
    token: Annotated[str, Depends(oauth2_scheme)],
    db: Session = Depends(get_session),
) -> User:
    cred_exc = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email = payload.get("sub")
        if not email:
            raise cred_exc
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token has expired", headers={"WWW-Authenticate": "Bearer"})
    except jwt.InvalidTokenError:
        raise cred_exc

    user = db.exec(select(User).where(User.email == email)).first()
    if not user:
        raise cred_exc
    return user
