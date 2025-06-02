from fastapi import APIRouter, Request, Depends, UploadFile, File, Form
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy.orm import Session
from database import model, script
from services.utility import get_staff_from_token, get_user_from_token
import os
import shutil

router = APIRouter(prefix="/profile", tags=["profile"])
templates = Jinja2Templates(directory="templates")

PROFILE_PIC_DIR = "static/uploads/profile_pictures"
os.makedirs(PROFILE_PIC_DIR, exist_ok=True)

def get_profile_pic_url(user):
    # Return a relative URL for use in templates
    if hasattr(user, "profile_picture_url") and user.profile_picture_url:
        # If already a relative/static path, just return it
        if user.profile_picture_url.startswith("static/"):
            return "/" + user.profile_picture_url.replace("\\", "/")
        # If it's an absolute path, get only the filename
        filename = os.path.basename(user.profile_picture_url)
        return filename
    return None

@router.get("/", response_class=HTMLResponse)
async def profile_page(request: Request, db: Session = Depends(script.get_db)):
    user = get_staff_from_token(request, db)
    admin = get_user_from_token(request, db)
    msg = []
    if user:
        user.profile_picture_url = get_profile_pic_url(user)
        msg.append("Welcome to your profile page!")
        return templates.TemplateResponse("profile.html", {"request": request, "user": user, "msg": msg})
    elif admin:
        msg.append("Welcome to the admin profile page!")
        admin_user = admin["user"]
        admin_user.profile_picture_url = get_profile_pic_url(admin_user)
        return templates.TemplateResponse("profile.html", {"request": request, "user": admin_user, "msg": msg})
    else:
        msg.append("SESSION EXPIRED, LOGIN AGAIN!.")
        return templates.TemplateResponse("login.html", {"request": request, "msg": msg})

@router.post("/upload-picture")
async def profile_upload_picture(request: Request, profile_picture: UploadFile = File(...), db: Session = Depends(script.get_db)):
    user = get_staff_from_token(request, db)
    admin = get_user_from_token(request, db)
    msg = []
    # Check if user or admin is logged in   
    if not user and not admin:
        msg.append("SESSION EXPIRED, LOGIN AGAIN!.")
        return templates.TemplateResponse("login.html", {"request": request, "msg": msg})
    target_user = user if user else admin["user"]
    # Delete previous picture if exists
    old_path = getattr(target_user, "profile_picture_url", None)
    if old_path and old_path.startswith("static/") and os.path.exists(old_path.replace("/", os.sep)):
        try:
            os.remove(old_path.replace("/", os.sep))
        except Exception:
            pass
    # Save new picture
    if user:
        filename = f"user_{user.id}_{profile_picture.filename}"
    else:
        filename = f"admin_{admin['user'].admin_name}_{profile_picture.filename}"
    file_path = os.path.join(PROFILE_PIC_DIR, filename)
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(profile_picture.file, buffer)
    target_user.profile_picture_url = f"static/uploads/profile_pictures/{filename}"
    db.commit()
    target_user.profile_picture_url = get_profile_pic_url(target_user)
    msg.append("Profile picture updated successfully.")
    return templates.TemplateResponse("profile.html", {"request": request, "user": target_user, "msg": msg})

@router.post("/delete-picture")
async def profile_delete_picture(request: Request, db: Session = Depends(script.get_db)):
    user = get_staff_from_token(request, db)
    admin = get_user_from_token(request, db)
    msg = []
    # Check if user or admin is still logged in
    if not user and not admin:
        msg.append("SESSION EXPIRED, LOGIN AGAIN!.")
    target_user = user if user else admin["user"]
    if not getattr(target_user, "profile_picture_url", None):
        msg.append("No profile picture to delete.")
        return templates.TemplateResponse("profile.html", {"request": request, "user": target_user, "msg": msg})
    file_path = target_user.profile_picture_url
    if file_path.startswith("static/"):
        file_path = file_path.replace("/", os.sep)
    if os.path.exists(file_path):
        os.remove(file_path)
    target_user.profile_picture_url = None
    db.commit()
    msg.append("Profile picture deleted successfully.")
    return templates.TemplateResponse("profile.html", {"request": request, "user": target_user, "msg": msg})

@router.post("/change-password")
async def profile_change_password(
    request: Request,
    current_password: str = Form(...),
    new_password: str = Form(...),
    confirm_password: str = Form(...),
    db: Session = Depends(script.get_db)
):
    msg = []
    from passlib.context import CryptContext
    pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
    
    user = get_staff_from_token(request, db)
    admin = get_user_from_token(request, db)
    
    target_user = user if user else (admin["user"] if admin else None)
    if not target_user:
        msg.append("SESSION EXPIRED, LOGIN AGAIN!.")
        return templates.TemplateResponse("profile.html", {"request": request, "user": None, "msg": msg})
    if not pwd_context.verify(current_password, target_user.password):
        
        msg.append("Current password is incorrect.")
        return templates.TemplateResponse("profile.html", {"request": request, "user": target_user, "msg": msg})
    if new_password != confirm_password:
        msg.append("Passwords do not match.")
        return templates.TemplateResponse("profile.html", {"request": request, "user": target_user, "msg": msg})
    target_user.password = pwd_context.hash(new_password)
    db.commit()
    msg.append("Password changed successfully. Please log in again.")
    # Do NOT call request.session.clear() unless SessionMiddleware is installed.
    return templates.TemplateResponse("login.html", {"request": request, "msg": msg})
