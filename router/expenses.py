from fastapi import APIRouter, Depends, Request, Form, status, HTTPException, File, UploadFile
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from database import model, script
from services.utility import get_staff_from_token
from fastapi.responses import HTMLResponse, JSONResponse
from services import keygen, utility, crud
from datetime import datetime
import json
from pydantic import ValidationError
import os

router = APIRouter(prefix="/expense", tags=["expense"])

templates = Jinja2Templates(directory="templates")

UPLOAD_DIR = "uploads/"
os.makedirs(UPLOAD_DIR, exist_ok=True)

async def save_attachment(attachment: UploadFile) -> str:
    try:
        file_location = f"static/uploads/{attachment.filename}"
        os.makedirs(os.path.dirname(file_location), exist_ok=True)
        with open(file_location, "wb") as f:
            f.write(await attachment.read())
        return file_location
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error saving attachment: {e}")

@router.get("/create", response_class=HTMLResponse)
async def create_expense(request: Request, db: Session = Depends(script.get_db)):
    msg = []
    user = utility.get_staff_from_token(request, db)
    admin = utility.get_user_from_token(request, db)

    if not user and not admin:
        msg.append("Session expired, LOGIN required")
        return templates.TemplateResponse(
            "login.html", {
                "request": request,
                "msg": msg,
            })
    if user:
        exid = str('ExID' + keygen.create_unique_random_key(db))
        return templates.TemplateResponse("expense_form.html", {
            "request": request,
            "msg": msg,
            "exid": exid,
            "user": user,
            "role": user.designation
        })
    else:
        msg.append("UNAUTHORIZED!, Sign in as a Staff to create an expense")
        return templates.TemplateResponse(
            "dashboard.html", {
                "request": request,
                "user": admin.get("user"),
                "role": admin.get("role"),
                "msg": msg,
            })

@router.post("/create", response_class=JSONResponse)
async def create_expense(
    request: Request,
    expense_input: str = Form(...),
    attachment: UploadFile = File(None),
    db: Session = Depends(script.get_db)
):
    try:
        expense_data = json.loads(expense_input)
    except (json.JSONDecodeError, ValidationError) as e:
        return JSONResponse(content={"message": f"Invalid input: {e}"}, status_code=400)

    attachment_path = await save_attachment(attachment) if attachment else None
    requestor = utility.get_staff_from_token(request, db)

    if not requestor:
        return JSONResponse(content={"message": "Session expired, LOGIN required"}, status_code=401)

    try:
        crud.create_expense(
            db=db,
            expense_number=expense_data["expense_number"],
            description=expense_data["description"],
            status="Pending",
            requestor_id=requestor.id,
            attachment_path=attachment_path,
            line_items_data=expense_data["line_items"],
            total=expense_data["total"]
        )
        return JSONResponse(content={"message": "Expense created successfully!"}, status_code=200)
    except Exception as e:
        return JSONResponse(content={"message": f"Error creating expense: {e}"}, status_code=500)

@router.get("/pending", response_class=HTMLResponse)
async def pending_expense(request: Request, db: Session = Depends(script.get_db)):
    msg = []
    user = utility.get_staff_from_token(request, db)
    admin = utility.get_user_from_token(request, db)

    if not user and not admin:
        msg.append("Session expired, LOGIN required")
        return templates.TemplateResponse(
            "login.html", {
                "request": request,
                "msg": msg,
            })
    if user:
        pending_expenses = db.query(model.Expense).filter(model.Expense.status == f"pending with {user.designation}").all()
        length_hint = len(pending_expenses)
        return templates.TemplateResponse("pending_expense.html", {
            "request": request,
            "msg": msg,
            "user": user,
            "role": user.designation,
            "pending_expenses": pending_expenses,
            "length_hint": length_hint,
        })
    else:
        msg.append("UNAUTHORIZED!, Sign in as a Staff to view expenses")
        return templates.TemplateResponse(
            "dashboard.html", {
                "request": request,
                "user": admin.get("user"),
                "role": admin.get("role"),
                "msg": msg,
            })

@router.get("/dash", response_class=HTMLResponse)
async def expense_dash(request: Request, db: Session = Depends(script.get_db)):
    msg = []
    user = utility.get_staff_from_token(request, db)
    admin = utility.get_user_from_token(request, db)

    if not user and not admin:
        msg.append("Session expired, LOGIN required")
        return templates.TemplateResponse(
            "login.html", {
                "request": request,
                "msg": msg,
            })
    if user:
        expenses = db.query(model.Expense).filter(model.Expense.requestor_id == user.id).all()
        return templates.TemplateResponse("expense_dash.html", {
            "request": request,
            "msg": msg,
            "user": user,
            "role": user.designation,
            "expenses": expenses,
        })
    else:
        msg.append("UNAUTHORIZED!, Sign in as a Staff to view expenses")
        return templates.TemplateResponse(
            "dashboard.html", {
                "request": request,
                "user": admin.get("user"),
                "role": admin.get("role"),
                "msg": msg,
            })

@router.post("/dash", response_class=HTMLResponse)
async def expense_dash_post(request: Request, db: Session = Depends(script.get_db)):
    return await expense_dash(request, db)

@router.get("/{expense_id}/preview", response_class=HTMLResponse)
async def preview_expense_modal(expense_id: int, request: Request, db: Session = Depends(script.get_db)):
    # ...existing code...
    expenseItems = db.query(model.ExpenseLineItem).filter(model.ExpenseLineItem.expense_id == expense_id).all()
    
    if not expenseItems:
        return JSONResponse(content={"status": "error", "message": "expenseItems not found!"}, status_code=404)
    
    # Confirm the structure being returned
    return JSONResponse(content={
        "status": "success",
        "expense": [
            {
                "id": items.id,
                "item_name": items.item_name,
                "quantity": items.quantity,
                "category": items.category,
                "price": items.price,
                "amount": items.amount,
            } for items in expenseItems
        ]
    })
