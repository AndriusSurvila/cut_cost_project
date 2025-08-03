
from pydantic import BaseModel, EmailStr, validator
from typing import Optional
from datetime import datetime

class UserCreate(BaseModel):
    username: str
    email: EmailStr
    password: str

    @validator('email')
    def validate_email_domain(cls, v):
        allowed_domains = ['gmail.com']
        domain = v.split('@')[-1]
        if domain not in allowed_domains:
            raise ValueError(f'Email domain must be one of {allowed_domains}')
        return v

class UserLogin(BaseModel):
    username: str
    password: str

class UserResponse(BaseModel):
    id: int
    username: str
    email: str
    is_active: bool
    created_at: datetime

    class Config:
        orm_mode = True

class Token(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"

class TokenRefresh(BaseModel):
    refresh_token: str

class UserUpdate(BaseModel):
    username: Optional[str] = None
    email: Optional[EmailStr] = None

    @validator('email')
    def validate_email_domain(cls, v):
        allowed_domains = ['gmail.com', 'yandex.ru']
        domain = v.split('@')[-1]
        if domain not in allowed_domains:
            raise ValueError(f'Email domain must be one of {allowed_domains}')
        return v

class PasswordChange(BaseModel):
    current_password: str
    new_password: str