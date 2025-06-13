
from fastapi import APIRouter, Depends, Request
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from database import model, script
from services import utility
from fastapi.responses import HTMLResponse

router = APIRouter(prefix="/dashboard", tags=["dashboard"])

templates = Jinja2Templates(directory="templates")

#dashboard page route
@router.get("/", response_class=HTMLResponse)
async def dashboard(
    request: Request,
    db:Session=Depends(script.get_db)
    ):
    
    msg = []
    
    admin_data = utility.get_user_from_token(request, db)    #return a dictionary       : mike.eziefule@gmail.com 
    staff_data = utility.get_staff_from_token(request, db)       #return user object    : mike.eziefule@gmail.com ifeanyi@gmail.com, 
    
    if not staff_data and not admin_data:
        msg.append("Session expired, LOGIN required")
        return templates.TemplateResponse(
        "login.html",{
        "request": request,
        "msg": msg,
        })
        
    if staff_data:
        all_requests = db.query(model.Requisition).filter(model.Requisition.requestor_id == staff_data.id).all() # Fetch all requisition unique to user
        expenses = db.query(model.Expense).filter(model.Expense.requestor_id == staff_data.id).all()
        request_length = len(all_requests)    
        expense_length = len(expenses)    
    
        return templates.TemplateResponse(
            "dashboard.html",{
            "request": request,
            "user": staff_data,
            "role": staff_data.designation,
            "all_requests": all_requests,
            "request_length": request_length,
            "expenses": expenses,
            "expense_length": expense_length,
            })
    
    if admin_data:
        all_requests = db.query(model.Requisition).filter(model.Requisition.requestor_id == admin_data["user"].id).all() # Fetch all requisition unique to user
        request_length = len(all_requests)    
        expenses = db.query(model.Expense).filter(model.Expense.requestor_id == admin_data["user"].id).all()
        expense_length = len(expenses)    
        
        return templates.TemplateResponse(
            "dashboard.html",{
            "request": request,
            "user": admin_data.get("user"),
            "role": admin_data.get("role"),
            "all_requests": all_requests,
            "request_length": request_length,
            "expenses": expenses,
            "expense_length": expense_length,
            })
