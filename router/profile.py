from fastapi import APIRouter, Request, Depends, UploadFile, File, Form
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy.orm import Session
from database import script
from services.utility import get_user_from_token
import os
from supabase_client import supabase
import tempfile
from pathlib import Path



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

    if not user_data:
        msg.append("SESSION EXPIRED, LOGIN AGAIN!.")
        return templates.TemplateResponse("signin.html", {"request": request, "msg": msg})

    bucket_name = "profile-pictures"
    new_filename = f"user_{user_data.id}_{profile_picture.filename}"
    bucket_path = f"profile_pictures/{new_filename}"

    # Save uploaded file to a temp location
    with tempfile.NamedTemporaryFile(delete=False) as tmp_file:
        file_bytes = await profile_picture.read()
        tmp_file.write(file_bytes)
        tmp_file_path = tmp_file.name

    if user_data.profile_picture_url:
        try:
            # Extract the path used in Supabase (after the bucket)
            old_path = user_data.profile_picture_url.split("/storage/v1/object/public/")[1]
            supabase.storage.from_(bucket_name).remove([old_path])
        except Exception:
            pass  # Ignore if not found or malformed

    try:
        # Upload the new picture to Supabase
        supabase.storage.from_(bucket_name).upload(
            path=bucket_path,
            file=tmp_file_path
        )

        # Get public URL
        public_url = supabase.storage.from_(bucket_name).get_public_url(bucket_path)

        # Update DB
        user_data.profile_picture_url = public_url
        db.commit()
        msg.append("Profile picture uploaded successfully.")
    
    except Exception as e:
        msg.append(f"Upload failed: {str(e)}")
    
    finally:
        Path(tmp_file_path).unlink(missing_ok=True)

    return templates.TemplateResponse("profile.html", {"request": request, "user": user_data, "msg": msg})

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
