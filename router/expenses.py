from fastapi import APIRouter, Depends, Request, Form, status, HTTPException, File, UploadFile
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from database import model, script
from fastapi.responses import HTMLResponse, JSONResponse
from services import keygen, crud, utility
from datetime import datetime
import json
from pydantic import ValidationError
import os
from schema.schematic import ExpenseInput
from services.responses import (
    signin_failed_response,
    expense_dash_response,
    pending_expense_response,
    create_expense_success_response,
    create_expense_failed_response,
)

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
    user = utility.get_user_from_token(request, db)
    admin = None  # Only use get_user_from_token for authentication

    if not user:
        msg.append("Session expired, LOGIN required")
        return templates.TemplateResponse(
            "signin.html", {
                "request": request,
                "msg": msg,
            })
    exid = str('ExID' + keygen.create_unique_random_key(db))
    return templates.TemplateResponse("expense_form.html", {
        "request": request,
        "msg": msg,
        "exid": exid,
        "user": user,
        "role": user.designation
    })

@router.post("/create", response_class=JSONResponse)
async def create_expense(
    request: Request,
    expense_input: str = Form(...),
    attachment: UploadFile = File(None),
    db: Session = Depends(script.get_db)
):
    
    """
    Create a new expense.

    Parameters:
    - request (Request): The HTTP request object.
    - expense_input (str): JSON string containing expense details.
    - attachment (UploadFile, optional): An optional file upload. If None, no attachment will be saved.
    - db (Session): Database session dependency.

    Returns:
    - JSONResponse: A response indicating success or failure of the expense creation.
    """
    
    try:
        #Validate and parse the input using the Pydantic model
        expense_obj = ExpenseInput.parse_raw(expense_input)
    except (json.JSONDecodeError, ValidationError) as e:
        return create_expense_failed_response(e)

    requestor = utility.get_user_from_token(request, db)
    
    if not requestor:
        return create_expense_failed_response("Session expired, LOGIN required", status_code=401)

    attachment_path = await save_attachment(attachment) if attachment else None
    line_manager = utility.get_line_manager(db, requestor)

    try:
        expense = crud.create_expense(
            db=db,
            expense_number=expense_obj.expense_number,
            description=expense_obj.description,
            status=f"pending with {line_manager.designation}" if line_manager else "pending with MD/CEO",
            requestor_id=requestor.id,
            attachment_path=attachment_path,
            line_items_data=expense_obj.line_items if expense_obj.line_items else None,
            total=expense_obj.total,
        )
        return create_expense_success_response()
    except Exception as e:
        return create_expense_failed_response(e)

@router.get("/pending", response_class=HTMLResponse)
async def pending_expense(request: Request, db: Session = Depends(script.get_db)):
    
    msg = []
    
    user_data = utility.get_user_from_token(request, db)
    
    if not user_data:
        msg.append("Session expired, LOGIN required")
        return signin_failed_response(request, msg)
    
    if user_data:
        # pending_expenses = db.query(model.Expense).filter(model.Expense.status == f"pending with {user_data.designation}").all()
        pending_expenses = db.query(model.Expense).join(model.Expense.requestor).filter(
        model.Expense.status == f"pending with {user_data.designation}",
        model.User.organization_id == user_data.organization_id
        ).all()
        
        length_hint = len(pending_expenses)
        all_users = db.query(model.User).filter(model.User.organization_id == user_data.organization_id).all()
        return pending_expense_response(
            request, user_data, pending_expenses, length_hint, all_users, msg
        )

@router.get("/dash", response_class=HTMLResponse)
async def expense_dash(request: Request, db: Session = Depends(script.get_db)):
    msg = []
    user_data = utility.get_user_from_token(request, db)
    
    if not user_data:
        msg.append("Session expired, LOGIN required")
        return signin_failed_response(request, msg)
    
    if user_data:
        expenses = db.query(model.Expense).filter(model.Expense.requestor_id == user_data.id).all()
        expense_length = len(expenses)
        all_users = db.query(model.User).filter(model.User.organization_id == user_data.organization_id).all()
        
        return expense_dash_response(
            request, user_data, expenses, expense_length, all_users
        )

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
    user = utility.get_user_from_token(request, db)

    if not user:
        return JSONResponse(content={"message": "Session expired, LOGIN required"}, status_code=401)

    expense = db.query(model.Expense).filter(model.Expense.id == id).first()

    if not expense:
        return JSONResponse(content={"status": "error", "message": "Expense not found!"}, status_code=404)

    try:
        user_cmd_level = int(user.cmd_level)
        line_manager = None

        # Try to find a line manager in the same department, one level lower at a time
        for level in range(user_cmd_level - 1, 0, -1):
            line_manager = db.query(model.User).filter(
                model.User.organization_id == user.organization_id,
                model.User.department == user.department,
                model.User.cmd_level == str(level).zfill(3)
            ).first()
            if line_manager:
                break

        # Fallback: search for any user with the required command level in the organization
        if not line_manager:
            for level in range(user_cmd_level - 1, 0, -1):
                line_manager = db.query(model.User).filter(
                    model.User.organization_id == user.organization_id,
                    model.User.cmd_level == str(level).zfill(3)
                ).first()
                if line_manager:
                    break

        if user.cmd_level == "001":
            expense.status = "Approved"
        else:
            expense.status = f"pending with {line_manager.designation}" if line_manager else "pending with MD/CEO"
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
    user = utility.get_user_from_token(request, db)

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
    
    user = utility.get_user_from_token(request, db)

    if not user:
        # return JSONResponse(content={"message": "Session expired, LOGIN required"}, status_code=401)
        msg.append("Session expired, LOGIN required")
        return templates.TemplateResponse(
            "signin.html", {
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
@router.post("/edit_expense", response_class=JSONResponse)
async def edit_expense(
    request: Request,
    expense_input: str = Form(...),
    attachment: UploadFile = File(None),
    db: Session = Depends(script.get_db)
):
    try:
        # Validate and parse the input using the Pydantic model
        expense_data = ExpenseInput.parse_raw(expense_input)
    except (json.JSONDecodeError, ValidationError) as e:
        return JSONResponse(content={"message": f"Invalid input: {e}"}, status_code=400)

    user = utility.get_user_from_token(request, db)

    if not user:
        return JSONResponse(content={"message": "Session expired, LOGIN required"}, status_code=401)

    expense = db.query(model.Expense).filter(
        model.Expense.expense_number == expense_data.expense_number,
        model.Expense.status == "Rejected"
    ).first()

    if not expense:
        return JSONResponse(content={"status": "error", "message": "Expense not found!"}, status_code=404)
    if expense.status != "Rejected":
        return JSONResponse(content={"status": "error", "message": "Expense is not editable!"}, status_code=400)

    try:
        expense.description = expense_data.description
        expense.total = expense_data.total

        db.query(model.ExpenseLineItem).filter(
            model.ExpenseLineItem.expense_id == expense.id).delete(synchronize_session=False)
        
        new_line_items = []
        for updated_item in expense_data.line_items:
            # updated_item is already a validated ExpenseLineItemInput object
            new_line_item = model.ExpenseLineItem(
                item_name=updated_item.item_name,
                quantity=updated_item.quantity,
                category=updated_item.category,
                price=updated_item.price,
                amount=updated_item.amount,
                expense_id=expense.id,
            )
            new_line_items.append(new_line_item)
        
        try:
            for item in new_line_items:
                db.add(item)
                try:
                    db.flush()  # Validate and check constraints for each item
                except Exception as e:
                    return JSONResponse(content={"status": "error", "message": f"Error saving line item: {e}"}, status_code=400)
        except Exception as e:
            return JSONResponse(content={"status": "error", "message": f"Error saving line items: {e}"}, status_code=500)

        expense.status = f"pending with {user.line_manager}"
        db.commit()
        
    except Exception as e:
        return JSONResponse(content={"status": "error", "message": f"Error updating Expenses: {e}"}, status_code=500)

# Route to delete a rejected expense
@router.post("/delete_expense", response_class=JSONResponse)
async def delete_expense(request: Request, id: int = Form(...), db: Session = Depends(script.get_db)):
    user = utility.get_user_from_token(request, db)

    if not user:
        return JSONResponse(content={"message": "Session expired, LOGIN required"}, status_code=401)

    expense = db.query(model.Expense).filter(
        model.Expense.id == id,
        model.Expense.status == "Rejected"
    ).first()

    if not expense:
        return JSONResponse(content={"status": "error", "message": "Requisition not found or not deletable!"}, status_code=404)

    try:
        expense_comments = db.query(model.ExpenseComment).filter(model.ExpenseComment.expense_id == id).all()
        for comment in expense_comments:
            db.delete(comment)
            db.commit()
            
        db.query(model.ExpenseLineItem).filter(model.ExpenseLineItem.expense_id == id).delete(synchronize_session=False)
        db.commit()
            
            
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