"""Setup the model schemas."""
from pydantic import BaseModel
# from datetime import date
from fastapi import Depends, Form
from fastapi.security import OAuth2PasswordRequestForm
from typing import Optional

class Token(BaseModel):
    access_token: str
    token_type: str
    


class ExtendedOAuth2PasswordRequestForm(OAuth2PasswordRequestForm):
    def __init__(
        self,
        username: str = Form(...),
        password: str = Form(...),
        role: Optional[str] = Form(None),  # New field
        # remember_me: Optional[bool] = Form(False),  # New field
    ):
        super().__init__(username=username, password=password, scope="", grant_type=None, client_id=None, client_secret=None)
        self.role = role
        # self.remember_me = remember_me