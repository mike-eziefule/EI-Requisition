from fastapi import APIRouter, Request, Depends, Form
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy.orm import Session
from database import script, model
from services import utility

router = APIRouter(prefix="/dashboard", tags=["dashboard"])
templates = Jinja2Templates(directory="templates")

#dashboard page route
@router.get("/", response_class=HTMLResponse)
async def dashboard(
    request: Request,
    db:Session=Depends(script.get_db)
    ):
    
    msg = []
    
    user_data = utility.get_user_from_token(request, db)    #return a dictionary       : mike.eziefule@gmail.com 
    
    if not user_data:
        msg.append("Session expired, Login required")
        return templates.TemplateResponse(
        "signin.html",{
        "request": request,
        "msg": msg,
        })
    
    if user_data:
        all_requests = db.query(model.Requisition).filter(model.Requisition.requestor_id == user_data.id).all() # Fetch all requisition unique to user
        expenses = db.query(model.Expense).filter(model.Expense.requestor_id == user_data.id).all()
        request_length = len(all_requests)    
        expense_length = len(expenses)    
    
        return templates.TemplateResponse(
            "dashboard.html",{
            "request": request,
            "user": user_data,
            "role": user_data.designation,
            "all_requests": all_requests,
            "request_length": request_length,
            "expenses": expenses,
            "expense_length": expense_length,
            })


@router.get("/settings", response_class=HTMLResponse)
async def settings_page(request: Request, db: Session = Depends(script.get_db)):
    user_data = utility.get_user_from_token(request, db)
    if not user_data or user_data.role != "administrator":
        return RedirectResponse(url="/login", status_code=302)
    # Scan all unique designations from User table
    designations = db.query(model.User.designation).distinct().all()
    designation_list = [d[0] for d in designations if d[0]]
    msg = ""
    if not designation_list:
        msg = "No staff designations found. Please add staff before setting approval hierarchy."
    return templates.TemplateResponse(
        "settings.html",
        {
            "request": request,
            "user": user_data,
            "role": user_data.role,
            "designation_list": designation_list,
            "msg": msg,
        }
    )

@router.post("/settings", response_class=HTMLResponse)
async def save_settings(
    request: Request,
    company_type: str = Form(...),
    positions: list[str] = Form(...),
    levels: list[int] = Form(...),
    db: Session = Depends(script.get_db)
):
    # Only allow admin users
    user_data = utility.get_user_from_token(request, db)
    if not user_data or user_data.role != "administrator":
        return RedirectResponse(url="/settings", status_code=302)
    # Here you would save the settings to the database or config
    # For now, just render the page with a success message
    msg = "Settings saved successfully!"
    return templates.TemplateResponse(
        "settings.html",
        {
            "request": request,
            "user": user_data,
            "role": user_data.role,
            "msg": msg,
            "company_type": company_type,
            "positions": positions,
            "levels": levels,
        }
    )
