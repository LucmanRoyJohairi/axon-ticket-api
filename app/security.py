import jwt
from datetime import datetime, timedelta, timezone
from pwdlib import PasswordHash
from pwdlib.hashers.argon2 import Argon2Hasher
from app.config import settings

#Configuration Constants
SECRET_KEY = settings.secret_key
ALGORITHM = settings.algorithm
ACCESS_TOKEN_EXPIRY_MINUTES = settings.access_token_expiry_minutes

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