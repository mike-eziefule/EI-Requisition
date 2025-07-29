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
        "signin.html",{
        "request": request,
        "msg": msg,
        })
        
    if user_data: 
        all_users = db.query(model.User).filter(model.User.organization_id == user_data.organization_id).all()
        staff_number = len(all_users)

        # Determine line manager for each user
        user_line_managers = {}
        
        for staff in all_users:
            try:
                staff_cmd_level = int(staff.cmd_level)
            except Exception:
                staff_cmd_level = None
                
            # Try to find a line manager in the same department, one level lower at a time

            if staff_cmd_level and staff_cmd_level > 1:
                # First, try to find in same department
                for i in range(staff_cmd_level - 1, 0, -1):
                    lm = db.query(model.User).filter(
                        model.User.organization_id == staff.organization_id,
                        model.User.department == staff.department,
                        model.User.cmd_level == str(i).zfill(3)
                    ).first()
                    if lm:
                        user_line_managers[staff.id] = lm
                        break
                    
                    # If not found, try any department in the org
                    if not lm:
                        for i in range(staff_cmd_level - 1, 0, -1):
                            
                            lm = db.query(model.User).filter(
                                model.User.organization_id == staff.organization_id,
                                model.User.cmd_level == str(i).zfill(3)
                                ).first()
                            if lm:
                                user_line_managers[staff.id] = lm
                                break
            else:
                user_line_managers[staff.id] = None

        return templates.TemplateResponse(
            "viewstaff.html",{
            "request": request,
            "msg":msg,
            "user": user_data,
            "role": user_data.designation,
            "all_users": all_users,
            "staff_number": staff_number,
            "user_line_managers": user_line_managers,
        })


