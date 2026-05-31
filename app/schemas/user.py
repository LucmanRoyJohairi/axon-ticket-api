from pydantic import BaseModel, EmailStr

class UserCreate(BaseModel):
    email: EmailStr
    password: str
    full_name: str | None

#login
class UserRequest(BaseModel):
    email: EmailStr
    password: str

class UserResponse(BaseModel):
    id: str
    email: str
    full_name: str | None
    is_admin: bool

    class config:
        from_attributes: True

#data format for a successful login response
class Token(BaseModel):
    access_token: str
    token_type: str