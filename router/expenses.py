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
from schema import schematic

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
            status=f"pending with {requestor.line_manager}",
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
            "expenses": expenses
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


# Route to approve a requisition
@router.post("/approve_expense", response_class=JSONResponse)
async def approve_expense(request: Request, id: int = Form(...), db: Session = Depends(script.get_db)):
    user = utility.get_staff_from_token(request, db)

    if not user:
        return JSONResponse(content={"message": "Session expired, LOGIN required"}, status_code=401)

    expense = db.query(model.Expense).filter(model.Expense.id == id).first()

    if not expense:
        return JSONResponse(content={"status": "error", "message": "Requisition not found!"}, status_code=404)

    try:
        if user.designation == "Storekeeper":
            expense.status = "Approved"
        else:
            expense.status = f"pending with {user.line_manager}"
        db.commit()
        return JSONResponse(content={"status": "success", "message": "Expense has been approved!"})
    except Exception as e:
        return JSONResponse(content={"status": "error", "message": f"Error approving expense: {e}"}, status_code=500)


# Route to reject a requisition
@router.post("/reject_expense", response_class=JSONResponse)
async def reject_expense(
    request: Request,
    id: int = Form(...),
    comment: str = Form(...),
    db: Session = Depends(script.get_db)
):
    user = utility.get_staff_from_token(request, db)

    if not user:
        return JSONResponse(content={"message": "Session expired, LOGIN required"}, status_code=401)

    expense = db.query(model.Expense).filter(model.Expense.id == id).first()

    if not expense:
        return JSONResponse(content={"status": "error", "message": "Expense not found!"}, status_code=404)

    try:
        expense.status = "Rejected"
        new_comment = model.ExpenseComment(
            expense_id=expense.id,
            comment=comment,
            created_by=user.email
        )
        db.add(new_comment)
        db.commit()
        return JSONResponse(content={"status": "success", "message": "Expenses rejected with comment!"})
    except Exception as e:
        return JSONResponse(content={"status": "error", "message": f"Error rejecting expenses: {e}"}, status_code=500)



# FastAPI route for rendering edit requisition form
@router.get("/edit-expense/{id}", response_class=HTMLResponse)
async def edit_expense(
    id: int,
    request: Request,
    db: Session = Depends(script.get_db)
):
    msg = []
    
    user = utility.get_staff_from_token(request, db)

    if not user:
        # return JSONResponse(content={"message": "Session expired, LOGIN required"}, status_code=401)
        msg.append("Session expired, LOGIN required")
        return templates.TemplateResponse(
            "login.html", {
                "request": request,
                "msg": msg,
            })
        
    expense = db.query(model.Expense).filter(model.Expense.id == id).first()
    if not expense:
        # return JSONResponse(content={"message": "Expense not found"}, status_code=404)
        msg.append("Expense not found")
        return templates.TemplateResponse(
        "pending_expense.html",
        {
            "request": request,
            "expense": expense,
            "msg": msg,
            "user": user,
            "role": user.designation
        },
    )
    return templates.TemplateResponse(
        "edit_expense_form.html",
        {
            "request": request,
            "expense": expense,
            "msg": [],
            "user": user,
        },
    )

# Route to edit a rejected requisition
@router.post("/edit-expense", response_class=JSONResponse)
async def edit_expense(
    request: Request,
    expense_input: str = Form(...),
    attachment: UploadFile = File(None),
    db: Session = Depends(script.get_db)
):
    try:
        expense_data = json.loads(expense_input)
        updated_expense = schematic.ExpenseInput(**expense_data)
    except (json.JSONDecodeError, ValidationError) as e:
        return JSONResponse(content={"message": f"Invalid input: {e}"}, status_code=400)

    user = utility.get_staff_from_token(request, db)

    if not user:
        return JSONResponse(content={"message": "Session expired, LOGIN required"}, status_code=401)

    expense = db.query(model.Expense).filter(
        model.Expense.expense_number == updated_expense.expense_number,
        model.Expense.status == "Rejected"
    ).first()

    if not expense:
        return JSONResponse(content={"status": "error", "message": "expense not found or not editable!"}, status_code=404)

    try:
        expense.description = updated_expense.description

        for updated_item in updated_expense.line_items:
            if updated_item.id:
                line_item = db.query(model.ExpenseLineItem).filter(
                    model.ExpenseLineItem.id == updated_item.id,
                    model.ExpenseLineItem.expense_id == expense.id
                ).first()
                if line_item:
                    line_item.item_name = updated_item.item_name
                    line_item.quantity = updated_item.quantity
                    line_item.category = updated_item.category
                    line_item.price = updated_item.price
                    line_item.amount = updated_item.amount
            else:
                new_line_item = model.ExpenseLineItem(
                    expense_id=expense.id,
                    item_name=updated_item.item_name,
                    quantity=updated_item.quantity,
                    category=updated_item.category,
                    price=updated_item.price,
                    amount=updated_item.amount
                )
                db.add(new_line_item)


        expense.status = f"pending with {user.line_manager}"
        db.commit()
        return JSONResponse(content={"status": "success", "message": "Expense updated successfully!"})
    except Exception as e:
        return JSONResponse(content={"status": "error", "message": f"Error updating Expenses: {e}"}, status_code=500)



# Route to delete a rejected requisition
@router.post("/delete_expense", response_class=JSONResponse)
async def delete_expense(request: Request, id: int = Form(...), db: Session = Depends(script.get_db)):
    user = utility.get_staff_from_token(request, db)

    if not user:
        return JSONResponse(content={"message": "Session expired, LOGIN required"}, status_code=401)

    expense = db.query(model.Expense).filter(
        model.Expense.id == id,
        model.Requisition.status == "Rejected"
    ).first()

    if not expense:
        return JSONResponse(content={"status": "error", "message": "Requisition not found or not deletable!"}, status_code=404)

    try:
        db.delete(expense)
        db.commit()
        return JSONResponse(content={"status": "success", "message": "Requisition deleted successfully!"})
    except Exception as e:
        return JSONResponse(content={"status": "error", "message": f"Error deleting requisition: {e}"}, status_code=500)





# Route to fetch expense details with comments
@router.get("/expense_details/{id}", response_class=JSONResponse)
async def expense_details(id: int, db: Session = Depends(script.get_db)):
    expense = db.query(model.Expense).filter(model.Expense.id == id).first()

    if not expense:
        return JSONResponse(content={"status": "error", "message": "Expense not found!"}, status_code=404)

    comments = db.query(model.ExpenseComment).filter(model.ExpenseComment.expense_id == id).all()

    def serialize_datetime(dt):
        if isinstance(dt, datetime):
            return dt.isoformat()
        return dt

    return JSONResponse(content={
        "status": "success",
        "expense": {
            "id": expense.id,
            "expense_number": expense.expense_number,
            "description": expense.description,
            "status": expense.status,
            "comments": [
                {
                    "comment": c.comment,
                    "created_by": c.created_by,
                    "created_at": serialize_datetime(c.created_at)
                } for c in comments
            ]
        }
    })