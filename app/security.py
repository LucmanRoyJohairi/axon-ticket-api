import jwt
from jwt.exceptions import InvalidTokenError, ExpiredSignatureError
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from datetime import datetime, timedelta, timezone
from pwdlib import PasswordHash
from pwdlib.hashers.argon2 import Argon2Hasher
from app.database import get_db
from app.config import settings
from app.models import User as UserModel
from app.schemas import TokenData
from sqlalchemy import select
from sqlalchemy.orm import Session


#Configuration Constants
SECRET_KEY = settings.secret_key
ALGORITHM = settings.algorithm
ACCESS_TOKEN_EXPIRY_MINUTES = settings.access_token_expiry_minutes

oauth2_scheme = OAuth2PasswordBearer(tokenUrl = "/auth/login")

#initialize Argon2 hasher
password_hash = PasswordHash((Argon2Hasher(),))

def hash_password(password: str):
    #convert plain text password into hash string
    return password_hash.hash(password)


def verify_password(password: str, hashed_password: str):
    #compares plain text pass against stored hash
    return password_hash.verify(password, hashed_password)


def create_access_token(data: dict, expires_delta: timedelta | None = None):
    #geneerate a secure, signed JWT token
    to_encode = data.copy()

    if(expires_delta):
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRY_MINUTES)

    to_encode.update({"exp" : expire})

    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


# Token Validation section
def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    credentials_exception = HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Could not validate credentials", headers={"WWW-Authenticate": "Bearer"})
    try:
        # decode the token using PyJWT
        payload = jwt.decode(
            token,
            SECRET_KEY,
            algorithms=[ALGORITHM]
        )
        
        # getting the user_id from the claims when it was created during the login stage, named the "sub" (subject) claim
        user_id: str = payload.get("sub")

        if user_id is None:
            raise credentials_exception
        
        # validate data matches our Pydantic schema structure
        token_data = TokenData(user_id=user_id)

    except ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has expired",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except InvalidTokenError:
         raise credentials_exception
    
    statement = select(UserModel).where(UserModel.id == token_data.user_id)
    result = db.execute(statement)
    user = result.scalar_one_or_none()

    if user is None:
        raise credentials_exception
    
    return user
