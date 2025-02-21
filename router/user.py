"""Routes related to User Account creation."""

from fastapi import APIRouter, Depends, Request, Form, status, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from database import model, script
from services.utility import bcrpyt_context, get_user_from_token
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from config import get_settings
from services import utility
from datetime import datetime




router = APIRouter(prefix="/user", tags=["auth"])

templates = Jinja2Templates(directory="templates")

#Home page
@router.get("/", response_class = HTMLResponse)
async def homepage(
    request:Request,
):
    return templates.TemplateResponse("index.html", {"request": request})

#register page route
@router.get("/register", response_class=HTMLResponse)
async def register(request: Request):
    return templates.TemplateResponse("register.html", {"request": request})

#NEW USER REGISTRATION
@router.post('/register', response_class=HTMLResponse)
async def register(
    request: Request, 
    organization_name: str = Form(...), 
    rc_number: str = Form(...), 
    address: str = Form(...),
    admin_name: str = Form(...), 
    email: str = Form(...),
    password: str = Form(...), 
    password2: str = Form(...),
    product: str = Form(...), 
    db:Session=Depends(script.get_db)
    ):
    
    msg = []
    
    if password != password2:
        msg.append("Passwords do not match")
        return templates.TemplateResponse("register.html", {
            "request": request, 
            "msg": msg,
            "organization_name": organization_name,  
            "rc_number": rc_number,
            "address": address,
            "admin_name": admin_name,
            'email': email,
            'password': password,
            'password2': password2,
            "product": product
        })
    
    if len(password) < 8:
        msg.append("Password should be > 6 character")
        return templates.TemplateResponse("register.html", {
            "request": request, 
            "msg": msg,
            "organization_name": organization_name,  
            "rc_number": rc_number,
            "address": address,
            "admin_name": admin_name,
            'email': email,
            'password': password,
            'password2': password2,
            "product": product
        })

    new_org = model.Organization(
        organization_name = organization_name,  
        rc_number = rc_number,
        address = address,
        admin_name = admin_name,
        email = email,
        product = product,
        password = bcrpyt_context.hash(password),
    )
    
    try:
        db.add(new_org)
        db.commit()
        db.refresh(new_org)
        msg.append("Registration successful")
        
        get_uuid = db.query(model.Organization).filter(model.Organization.email == email).first()
        
        msg.append("This is your Admin code, Please save it!: " + get_uuid.id)
        
        return templates.TemplateResponse("login.html", {
            "request": request, 
            "msg": msg,
        })
        
    except IntegrityError:
        msg.append("Email already taken")
        return templates.TemplateResponse("register.html", {
            "request": request, 
            "msg": msg,
            "organization_name": organization_name,  
            "rc_number": rc_number,
            "address": address,
            "admin_name": admin_name,
            'email': email,
            'password': password,
            'password2': password2,
            "product": product
        })
        


#add member page route
@router.get("/addmember", response_class=HTMLResponse)
async def addmember(request: Request):
    return templates.TemplateResponse("add_member.html", {"request": request})


#NEW USER REGISTRATION
@router.post('/addmember', response_class=HTMLResponse)
async def addmember(
    request: Request, 
    staff_name: str = Form(...), 
    designation: str = Form(...), 
    email: str = Form(...),
    password: str = Form(...), 
    password2: str = Form(...),
    db:Session=Depends(script.get_db)
    ):
    
    msg = []

    user = utility.get_user_from_token(request, db)

    admin_auth = db.query(model.Organization).filter(model.Organization.email == user['user'].email).first()

    if not admin_auth:
        msg.append("Contact your administrator, Try again!")
        return templates.TemplateResponse("login.html", {
            "request": request, 
            "msg": msg,
        })
    
    if password != password2:
        msg.append("Passwords do not match")
        return templates.TemplateResponse("add_member.html", {
            "request": request, 
            "msg": msg,
            "staff_name": staff_name,
            "designation": designation,
            'email': email,
            'password': password,
            'password2': password2,
        })
    
    if len(password) < 8:
        msg.append("Password should be > 6 character")
        return templates.TemplateResponse("add_member.html", {
            "request": request, 
            "msg": msg,
            "staff_name": staff_name,
            "designation": designation,
            'email': email,
            'password': password,
            'password2': password2,
        })

    new_staff = model.User(
        organization_name = admin_auth.organization_name, 
        staff_name = staff_name,
        designation = designation,
        email = email,
        password = bcrpyt_context.hash(password),
        date = datetime.now().date(),
        organization_id = admin_auth.id,
    )
    
    try:
        db.add(new_staff)
        db.commit()
        db.refresh(new_staff)
        msg.append("Registration successful")        
        return templates.TemplateResponse("add_member.html", {
            "request": request, 
            "msg": msg,
        })
        
    except IntegrityError:
        msg.append("Email already taken")
        return templates.TemplateResponse("add_member.html", {
            "request": request, 
            "msg": msg,
            "staff_name": staff_name,
            "designation": designation,
            'email': email,
            'password': password,
            'password2': password2,
        })




#add review ROUTE
@router.post("/post_review", response_class=HTMLResponse)
async def post_review(
    request: Request,
    # rating: str = Form(...),
    content: str = Form(...),
    name: str = Form(...),
    email: str = Form(...),
    db:Session=Depends(script.get_db)
):
    
    
    msg = []
    
    rating = "5"
    
    # authentication
    user = utility.get_user_from_token(request, db)
    
    # if not user:
    #     msg.append("Session Expired, Login again!")
    #     return templates.TemplateResponse("login.html", {"request": request, "msg": msg})
    
    #database dump
    save_review = model.Review(
        name=name,
        email=email,
        rating = rating,
        content = content,
        date = datetime.now().date()
    )
    db.add(save_review)
    db.commit()
    db.refresh(save_review)
    return RedirectResponse("/", status_code=status.HTTP_302_FOUND)

