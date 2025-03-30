"""Routes related to User Account creation."""

from fastapi import APIRouter, Depends, Request, Form, status
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from starlette.responses import RedirectResponse
from sqlalchemy.orm import Session
from database import model, script
from services import utility

router = APIRouter(tags=["link"])

templates = Jinja2Templates(directory="templates")

#Home page
@router.get("/", response_class = HTMLResponse)
async def index(
    request:Request,
):
    return templates.TemplateResponse("index.html", {"request": request})

#dashboard page route
@router.get("/dashboard", response_class=HTMLResponse)
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
    
    
# Route to fetch items that share the same category_id
@router.get("/category/{requisition_id}/items", response_model=list)
def get_items_by_category(
    requisition_id: int, 
    db:Session=Depends(script.get_db)
):
    # Fetch all items that have same Requisition_id
    items = db.query(model.LineItem).filter(model.LineItem.requisition_id == requisition_id).all()
    return [{
        "id": item.id, 
        "item_name": item.item_name, 
        "quantity": item.quantity, 
        "category": item.category, 
        "item_reason": item.item_reason
        } for item in items]

#dashboard page route
@router.get("/admin_view_all", response_class=HTMLResponse)
async def admin_view_all(
    request: Request,
    db:Session=Depends(script.get_db)
    ):
    
    msg = []
    
    user_data = utility.get_user_from_token(request, db)
    
    if not user_data:
        msg.append("Session expired, LOGIN required")
        return templates.TemplateResponse(
        "login.html",{
        "request": request,
        "msg": msg,
        })
        
    if user_data["role"] != "administrator":
        
        msg.append("Contact your administrator")
        return templates.TemplateResponse(
        "dashboard.html",{
        "request": request,
        "msg": msg,
        "user": user_data["user"],
        "role": user_data["role"]
        })
        
    all_users = db.query(model.User).filter(model.User.organization_id == user_data["user"].id ).all()
    staff_number = len(all_users)
    
    
    return templates.TemplateResponse(
        "viewstaff.html",{
        "request": request,
        "msg":msg,
        "user": user_data.get("user"),
        "role": user_data.get("role"),
        "all_users": all_users,
        "staff_number": staff_number
        })


