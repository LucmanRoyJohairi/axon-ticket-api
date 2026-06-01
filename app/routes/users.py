from fastapi import APIRouter
from fastapi import Depends, HTTPException
from fastapi.security import OAuth2PasswordRequestForm
from schemas import UserCreate, UserResponse, Token
from app.database import get_db
from app.models import User as UserModel
from app.models import *
from sqlalchemy import select
from sqlalchemy.orm import Session
from security import hash_password, verify_password, create_access_token

router = APIRouter(
    prefix="/auth",
    tags=["auth"]
)

# Registration
@router.post("/register", response_model=UserResponse)
def register_user(payload: UserCreate, db: Session = Depends(get_db)):
    statement = select(UserModel).where(UserModel.email == payload.email)
    result = db.execute(statement)
    matching_user = result.scalar_one_or_none()

    if matching_user:
        raise HTTPException(status_code=400, detail="email already in use")
    
    hashed = hash_password(payload.password)

    new_user = UserModel(
        email=payload.email,
        hashed_password=hashed,
        full_name=payload.full_name
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    return new_user


@router.post("/login", response_model=Token)
def login_user(payload: OAuth2PasswordRequestForm = Depends() , db: Session = Depends(get_db)):
    # OAuth2 spec uses 'username'. In your app, this maps to the user's email.
    statement = select(UserModel).where(UserModel.email == payload.username)
    result = db.execute(statement)
    matching_user = result.scalar_one_or_none()

    # Mitigate timing attacks by executing a dummy verify if user doesn't exist
    if matching_user is None:
        verify_password(payload.password, "dummy_hash_to_prevent_timing_attacks")
        raise HTTPException(status_code=404, detail="Email or Password is incorrect")

    is_valid = verify_password(payload.password, matching_user.hashed_password)

    if not is_valid:
        raise HTTPException(status_code=404, detail="Email or Password is incorrect")

    # generate access token and return JWT
    # Use stringified user ID for the 'sub' claim for better database longevity
    access_token = create_access_token(data={"sub": str(matching_user.id)})
    return {
        "access_token": access_token,
        "token_type": "bearer", 
    }