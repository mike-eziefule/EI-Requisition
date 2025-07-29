"""Routes related to User Account creation."""

from fastapi import APIRouter, Depends, Request, Form
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from database import model, script
from services.utility import bcrpyt_context, get_user_from_token
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from config import get_settings
from services import crud, utility
from services.responses import (
    registration_failed_response,
    registration_success_response,
    add_member_failed_response,
    add_member_success_response,
)

from datetime import datetime


router = APIRouter(prefix="/user", tags=["user"])

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
    product: str = Form(...),
    owner_name: str = Form(...),
    owner_designation: str = Form(...),
    email: str = Form(...),
    owner_password: str = Form(...),
    password2: str = Form(...),
    owner_role: str = Form(...),
    db:Session=Depends(script.get_db)
    ):
    msg = []

    # Password validation
    if not utility.validate_password(owner_password, password2, msg):
        return registration_failed_response(
            request, msg, organization_name, rc_number, address, owner_name,
            owner_designation, email, owner_password, password2, owner_role, product
        )

    # Create Organization and Owner User
    try:
        new_org = crud.create_organization(db, organization_name, rc_number, address, product)
        new_owner = crud.create_owner_user(
            db=db,
            organization_name=organization_name,
            staff_name=owner_name,
            designation=owner_designation,
            email=email,
            password=owner_password,
            role=owner_role,
            organization_id=new_org.id
        )
        msg.append("Registration successful")
        return registration_success_response(request, msg)
    except IntegrityError:
        db.rollback()
        msg.append("Email already taken")
        return registration_failed_response(
            request, msg, organization_name, rc_number, address, owner_name,
            owner_designation, email, owner_password, password2, owner_role, product
        )

#add member page route
@router.get("/addmember", response_class=HTMLResponse)
async def addmember(request: Request, db:Session=Depends(script.get_db)):
    
    msg = []

    user = utility.get_user_from_token(request, db)
    

    if not user:
        msg.append("Session Expired, Login again!")
        return templates.TemplateResponse("signin.html", {
            "request": request, 
            "msg": msg,
            
        })
    if user.role != 'administrator':
        msg.append("Contact your administrator, Try again!")
        return templates.TemplateResponse("dashboard.html", {
            "request": request, 
            "msg": msg,
            "user": user,
            "role": user.designation
        })
        
    all_users = db.query(model.User).filter(model.User.organization_id == user.organization_id ).all()
    staff_number = len(all_users)
    
    return templates.TemplateResponse(
        "add_member.html", {
            "request": request, 
            "msg": msg,
            "user": user,
            "role": user.designation,
            "staff_number": staff_number
        })


#NEW USER REGISTRATION
@router.post('/addmember', response_class=HTMLResponse)
async def addmember(
    request: Request, 
    staff_name: str = Form(...), 
    designation: str = Form(...), 
    email: str = Form(...),
    password: str = Form(...), 
    password2: str = Form(...),
    role: str = Form(...),
    cmd_level: str = Form(...), 
    department: str = Form(...),
    db:Session=Depends(script.get_db)
    ):
    msg = []

    user = utility.get_user_from_token(request, db)
    
    if not user:
        msg.append("Session Expired, login again")
        return templates.TemplateResponse("signin.html", {
            "request": request, 
            "msg": msg,
        })
        
    if user.role != "administrator":
        msg.append("Contact your administrator")
        return templates.TemplateResponse(
        "dashboard.html",{
        "request": request,
        "msg": msg,
        "user": user,
        "role": user.designation
        })
        
    role_check = db.query(model.User).filter(model.User.designation == designation, model.User.department == department).first()
    if role_check:
        msg.append("Role already occupied by {role_check.staff_name}")
        return add_member_failed_response(
            request, msg, staff_name, designation, cmd_level, role, email, password, password2, user, department
        )
    if password != password2:
        msg.append("Passwords do not match")
        return add_member_failed_response(
            request, msg, staff_name, designation, cmd_level, role, email, password, password2, user, department
        )
    if len(password) < 8:
        msg.append("Password should be at least 8 characters long")
        return add_member_failed_response(
            request, msg, staff_name, designation, cmd_level, role, email, password, password2, user, department
        )
    
    new_staff = model.User(
        organization_name = user.organization_name, 
        staff_name = staff_name,
        designation = designation,
        email = email,
        password = bcrpyt_context.hash(password),
        role = role,
        date = datetime.now().date(),
        organization_id = user.organization_id,
        cmd_level = cmd_level,
        department = department
    )
    
    try:
        db.add(new_staff)
        db.commit()
        db.refresh(new_staff)
        msg.append("Registration successful")
        
        all_users = db.query(model.User).filter(model.User.organization_id == user.organization_id ).all()
        staff_number = len(all_users)
        
        # Determine line manager for each user
        user_line_managers = {}
        for staff in all_users:
            try:
                staff_cmd_level = int(staff.cmd_level)
            except Exception:
                staff_cmd_level = None
            if staff_cmd_level and staff_cmd_level > 1:
                # First, try to find in same department
                lm = db.query(model.User).filter(
                    model.User.organization_id == staff.organization_id,
                    model.User.department == staff.department,
                    model.User.cmd_level == str(staff_cmd_level - 1).zfill(3)
                ).first()
                # If not found, try any department in the org
                if not lm:
                    lm = db.query(model.User).filter(
                        model.User.organization_id == staff.organization_id,
                        model.User.cmd_level == str(staff_cmd_level - 1).zfill(3)
                    ).first()
                user_line_managers[staff.id] = lm
            else:
                user_line_managers[staff.id] = None

        return add_member_success_response(
            request, msg, user, staff_number, all_users, user_line_managers
        )
    except IntegrityError:
        db.rollback()
        msg.append("Email already taken")
        return add_member_failed_response(
            request, msg, staff_name, designation, cmd_level, role, email, password, password2, user, department
        )

# remove member page route
@router.get("/removemember/{id}", response_class=HTMLResponse)
async def removemember(request: Request, db: Session = Depends(script.get_db)):
    
    msg = []
    
    user = utility.get_user_from_token(request, db)
    
    if user.role != 'administrator':
        msg.append("Contact your administrator, Try again!")
        return templates.TemplateResponse("dashboard.html", {
            "request": request, 
            "msg": msg,
        })
        
    target_users = db.query(model.User).filter(model.User.id == id ).first()
    if not target_users:
        msg.append("User not found")
        return templates.TemplateResponse("viewstaff.html", {
            "request": request, 
            "msg": msg,
            "user": user,
            "role": user.designation
        })
    
    return templates.TemplateResponse("remove_member.html", {
        "request": request,
        "msg": msg,
        "user": user,
        "role": user.designation,
        "target_user": target_users,
    })