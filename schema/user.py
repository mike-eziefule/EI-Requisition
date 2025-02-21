""" schema validation for user route"""
from pydantic import EmailStr, BaseModel
from fastapi import Request
from typing import Optional

# class BaseUser(BaseModel):
#     email : EmailStr
    
# class UserLogin(BaseUser):
#     username : str
    
# class UserCreate(UserLogin):
#     password: str
    
# class editUser(BaseModel):
#     username: str
    
        
class Token(BaseModel):
    access_token: str
    token_type: str
    
class LoginForm:
    def __init__(self, request: Request):
        self.request: Request = request
        self.username: Optional[str] = None
        self.password: Optional[str] = None
        self.role: Optional[str] = None
        
    async def create_auth_form(self):
        form = await self.request.form()
        self.username = form.get("email")
        self.password = form.get("password")
        self.role = form.get("role")