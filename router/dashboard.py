
from fastapi import APIRouter, Depends, Request
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from database import model, script
from services import utility
from fastapi.responses import HTMLResponse

router = APIRouter(prefix="/dashboard", tags=["dashboard"])

templates = Jinja2Templates(directory="templates")

#dashboard page route
@router.get("/user", response_class=HTMLResponse)
async def dashboard(
    request: Request,
    db:Session=Depends(script.get_db)
    ):
    
    msg = []
    
    user_data = utility.get_user_from_token(request, db)    #return a dictionary
    owner =  utility.get_staff_from_token(request, db)       #return user object
    
    if not user_data and not owner:
        msg.append("Session expired, LOGIN required")
        return templates.TemplateResponse(
        "login.html",{
        "request": request,
        "msg": msg,
        })
    
    if user_data:
        all_requests = db.query(model.Requisition).filter(model.Requisition.requestor_id == user_data['user'].id).all() # Fetch all requisition unique to user
        length_hint = len(all_requests)
        
        return templates.TemplateResponse(
            "dashboard.html",{
            "request": request,
            "user": user_data.get("user"),
            "role": user_data.get("role"),
            "all_requests": all_requests,
            "length_hint": length_hint,
            })
    
    if owner:
        all_requests = db.query(model.Requisition).filter(model.Requisition.requestor_id == user_data['user']).all() # Fetch all requisition unique to user
        length_hint = len(all_requests)    
    
        return templates.TemplateResponse(
            "dashboard.html",{
            "request": request,
            "user": user_data.get("user"),
            "role": user_data.get("role"),
            "all_requests": all_requests,
            "length_hint": length_hint,
            })
