from fastapi import APIRouter, Request, Depends, UploadFile, File, Form
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy.orm import Session
from database import script
from services.utility import get_user_from_token
import os
from supabase_client import supabase
from io import BytesIO


router = APIRouter(prefix="/profile", tags=["profile"])

templates = Jinja2Templates(directory="templates")

PROFILE_PIC_DIR = "static/uploads/profile_pictures"
os.makedirs(PROFILE_PIC_DIR, exist_ok=True)


def get_profile_pic_url(user):
    if hasattr(user, "profile_picture_url") and user.profile_picture_url:
        if user.profile_picture_url.startswith("static/"):
            # Local/static file (legacy or fallback)
            return "/" + user.profile_picture_url.replace("\\", "/")
        else:
            # Hosted on Supabase – assume the filename is stored
            bucket_name = "profile-pictures"
            public_url = supabase.storage.from_(bucket_name).get_public_url(user.profile_picture_url)
            return public_url
    return None

@router.get("/", response_class=HTMLResponse)
async def profile_page(request: Request, db: Session = Depends(script.get_db)):
    user_data = get_user_from_token(request, db)
    msg = []

    if user_data:
        # Fetch the profile picture URL (Supabase public URL or static)
        user_data.profile_picture_url = get_profile_pic_url(user_data)

        msg.append("Welcome to your profile page!")
        return templates.TemplateResponse("profile.html", {
            "request": request,
            "user": user_data,
            "msg": msg
        })
    else:
        msg.append("SESSION EXPIRED, LOGIN AGAIN!.")
        return templates.TemplateResponse("signin.html", {
            "request": request,
            "msg": msg
        })
        
        
@router.post("/upload-picture")
async def profile_upload_picture(
    request: Request, 
    profile_picture: UploadFile = File(...), 
    db: Session = Depends(script.get_db)
):
    
    user_data = get_user_from_token(request, db)
    msg = []
    
    # Check if user or admin is logged in   
    if not user_data:
        msg.append("SESSION EXPIRED, LOGIN AGAIN!.")
        return templates.TemplateResponse("signin.html", {"request": request, "msg": msg})
    
    
    # Upload to Supabase bucket
    bucket_name = "profile-pictures"
    filename = f"user_{user_data.id}_{profile_picture.filename}"
    bucket_path = f"profile_pictures/{filename}"
    file_bytes = await profile_picture.read()

    # Optional: Delete old picture (if exists)
    try:
        supabase.storage.from_(bucket_name).remove([bucket_path])
    except Exception:
        pass  # it's okay if file doesn't exist
    
    try:
        # Upload the file to Supabase storage
        supabase.storage.from_(bucket_name).upload(
            path=bucket_path,
            file=BytesIO(file_bytes),
        )
        
        public_url = supabase.storage.from_(bucket_name).get_public_url(bucket_path)
        
    except Exception as e:
        msg.append(f"Upload failed: {str(e)}")
        return templates.TemplateResponse("profile.html", {"request": request, "user": user_data, "msg": msg})

    # Update user in DB
    user_data.profile_picture_url = public_url
    db.commit()
    
    msg.append("Profile picture updated successfully.")
    return templates.TemplateResponse("profile.html", {"request": request, "user": user_data, "msg": msg})


@router.post("/delete-picture")
async def profile_delete_picture(request: Request, db: Session = Depends(script.get_db)):
    user_data = get_user_from_token(request, db)
    msg = []
    # Check if user or admin is still logged in
    if not user_data:
        msg.append("SESSION EXPIRED, LOGIN AGAIN!.")
        
    target_user = user_data
    
    file_url = getattr(target_user, "profile_picture_url", None)

    if not file_url:
        msg.append("No profile picture to delete.")
        return templates.TemplateResponse("profile.html", {"request": request, "user": target_user, "msg": msg})

    try:
        # Extract the filename from the public URL
        filename = file_url.split("/")[-1]
        bucket_name = "profile-pictures"

        # Delete from Supabase bucket
        supabase.storage.from_(bucket_name).remove([filename])

        # Clear from database
        target_user.profile_picture_url = None
        db.commit()

        msg.append("Profile picture deleted successfully.")
    except Exception as e:
        msg.append(f"Failed to delete profile picture: {str(e)}")

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
    
    user_data = get_user_from_token(request, db)
    
    target_user = user_data if user_data else None
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
    return templates.TemplateResponse("signin.html", {"request": request, "msg": msg})
