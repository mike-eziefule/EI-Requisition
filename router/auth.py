"""Routes related to Authentication and Authorization."""
from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException, Request, Response, Form
from starlette import status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from starlette.responses import RedirectResponse
from sqlalchemy.orm import Session
from database import script
from schema import app, user
from datetime import timedelta
from database.script import db_session
from services import utility

router = APIRouter(prefix="/auth", tags=["auth"])
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/token")

templates = Jinja2Templates(directory="templates")


#USER TOKEN GENERATION
@router.post("/token", response_model= app.Token)
async def login_for_access_token(
    response: Response, 
    form_data:Annotated[app.ExtendedOAuth2PasswordRequestForm, Depends()], 
    db:db_session
    ):
    
    token = utility.authenticate_user(form_data.username, form_data.password, form_data.role, timedelta(minutes=60), db)
    
    if token == False:
        return False
        
    response.set_cookie(key="access_token", value = token, httponly=True)
    
    return True



#login get page route
@router.get("/login", response_class=HTMLResponse)
async def login(request: Request):
    
    return templates.TemplateResponse("login.html", {"request": request})

#login post page route
@router.post("/login", response_class=HTMLResponse)
async def postlogin(
    request:Request, 
    db:Session=Depends(script.get_db)
    ):
    
    msg = []
    
    try:
        form = user.LoginForm(request)
        await form.create_auth_form()
        response = RedirectResponse("/dashboard", status_code=status.HTTP_302_FOUND)
        
        validate_user_cookie = await login_for_access_token(response=response, form_data=form, db=db)
        
        if not validate_user_cookie:
            msg.append("Incorrect role or Login credentials")
            return templates.TemplateResponse("login.html", {
                "request": request, 
                "msg": msg, 
                "email": form.username,
                "role": form.role
            })
        
        return response
    except HTTPException:
        msg.append("Unknown error")
        return templates.TemplateResponse("login.html", {
            "request": request, 
            "msg": msg,
            "email": form.username
            })
    

#logout page route
@router.get("/logout", response_class=HTMLResponse)
async def logout(request: Request):
    
    msg = []
    
    msg.append("Logout successful")
    response = templates.TemplateResponse("index.html", {"request": request, "msg": msg})
    response.delete_cookie(key="access_token")
    return response