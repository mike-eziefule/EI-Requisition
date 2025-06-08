"""Routes related to requisitions."""

from fastapi import APIRouter, Depends, Request, Form, status, HTTPException, File, UploadFile
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from database import model, script
from services.utility import get_staff_from_token
from fastapi.responses import HTMLResponse, JSONResponse
from config import get_settings
from services import keygen, utility, crud
from datetime import datetime
import json
from pydantic import ValidationError
import os
from schema.schematic import RequisitionInput

router = APIRouter(prefix="/requisition", tags=["requisition"])

templates = Jinja2Templates(directory="templates")

#dashboard page route
@router.get("/request_dash", response_class=HTMLResponse)
async def request_dash(
    request: Request,
    db:Session=Depends(script.get_db)
    ):
    
    msg = []
    
    admin_data = utility.get_user_from_token(request, db)    #return a dictionary
    user_data =  utility.get_staff_from_token(request, db)       #return user object
    
    if not user_data and not admin_data:
        msg.append("Session expired, LOGIN required")
        return templates.TemplateResponse(
        "login.html",{
        "request": request,
        "msg": msg,
        })
    
    if user_data:
        all_requests = db.query(model.Requisition).filter(model.Requisition.requestor_id == user_data.id).all() # Fetch all requisition unique to user
        request_length = len(all_requests)
        
        return templates.TemplateResponse(
            "request_dash.html",{
            "request": request,
            "user": user_data,
            "role": user_data.designation,
            "all_requests": all_requests,
            "request_length": request_length,
            })
    
    if admin_data:        
        
        msg.append("UNAUTHORIZED!, Sign in as a Staff to create a requisition")
        all_requests = db.query(model.Requisition).filter(model.Requisition.requestor_id == "not allowed").all() # Fetch all requisition unique to user
        request_length = len(all_requests)    
        expenses = db.query(model.Expense).filter(model.Expense.requestor_id == "not allowed").all()
        expense_length = len(expenses)    
        
        return templates.TemplateResponse(
            "dashboard.html",{
            "msg": msg,
            "request": request,
            "user": admin_data.get("user"),
            "role": admin_data.get("role"),
            "all_requests": all_requests,
            "request_length": request_length,
            "expenses": expenses,
            "expense_length": expense_length,
            })

#dashboard page route
@router.get("/request_history", response_class=HTMLResponse)
async def request_history(
    request: Request,
    db:Session=Depends(script.get_db)
    ):
    
    msg = []
    
    admin_data = utility.get_user_from_token(request, db)    #return a dictionary
    user_data =  utility.get_staff_from_token(request, db)       #return user object
    
    if not user_data and not admin_data:
        msg.append("Session expired, LOGIN required")
        return templates.TemplateResponse(
        "login.html",{
        "request": request,
        "msg": msg,
        })
    
    if user_data:
        all_requests = db.query(model.Requisition).filter(model.Requisition.requestor_id == user_data.id, model.Requisition.status == "Approved" ).all() # Fetch all requisition unique to user
        request_length = len(all_requests)
        
        return templates.TemplateResponse(
            "request_dash.html",{
            "request": request,
            "user": user_data,
            "role": user_data.designation,
            "all_requests": all_requests,
            "request_length": request_length,
            })
    
    if admin_data:        
        
        msg.append("UNAUTHORIZED!, Sign in as a Staff to create a requisition")
        all_requests = db.query(model.Requisition).filter(model.Requisition.requestor_id == "not allowed").all() # Fetch all requisition unique to user
        request_length = len(all_requests)    
        expenses = db.query(model.Expense).filter(model.Expense.requestor_id == "not allowed").all()
        expense_length = len(expenses)    
        
        return templates.TemplateResponse(
            "dashboard.html",{
            "msg": msg,
            "request": request,
            "user": admin_data.get("user"),
            "role": admin_data.get("role"),
            "all_requests": all_requests,
            "request_length": request_length,
            "expenses": expenses,
            "expense_length": expense_length,
            })

# Route to create a new requisition (GET)
@router.get("/create-requisition", response_class=HTMLResponse)
async def create_requisition(request: Request, db: Session = Depends(script.get_db)):
    
    msg = []
    
    user = utility.get_staff_from_token(request, db)
    admin = utility.get_user_from_token(request, db)

    if not user and not admin:
        msg.append("Session expired, LOGIN required")
        return templates.TemplateResponse(
        "login.html",{
        "request": request,
        "msg": msg,
        })
        
    if user:
        # Generate a unique request number
        reid = str('ReID' + keygen.create_unique_random_key(db))
        
        return templates.TemplateResponse("request_form.html",{
            "request": request,
            "msg": msg,
            "reid": reid,
            "user": user,
            "role": user.designation}
        )
    else:
        
        msg.append("UNAUTHORIZED!, Sign in as a Staff to create a requisition")
        
        return templates.TemplateResponse(
            "dashboard.html",{
            "request": request,
            "user": admin.get("user"),
            "role": admin.get("role"),
            "msg": msg,
            })



# Route to create a new requisition (POST)
@router.post("/create-requisition", response_class=JSONResponse)
async def create_requisition(
    request: Request,
    requisition_input: str = Form(...),
    db: Session = Depends(script.get_db)
):  
    try:
        requisition_obj = RequisitionInput.parse_raw(requisition_input)
        # Debug: print the parsed object
        print("Parsed requisition_obj:", requisition_obj)
    except (json.JSONDecodeError, ValidationError) as e:
        print("Validation error:", e)
        return JSONResponse(content={"message": f"Invalid input: {e}"}, status_code=400)

    requestor = utility.get_staff_from_token(request, db)

    if not requestor:
        return JSONResponse(content={"message": "Session expired, LOGIN required"}, status_code=401)

    try:
        requisition = crud.create_requisition(
            db=db,
            request_number=requisition_obj.request_number,
            description=requisition_obj.description,
            status=f"pending with {requestor.line_manager}",
            requestor_id=requestor.id,
            line_items_data=requisition_obj.line_items,
        )
        return JSONResponse(content={"message": "Requisition created successfully!"}, status_code=200)
    except Exception as e:
        print("Server error:", e)
        return JSONResponse(content={"message": f"Error creating requisition: {e}"}, status_code=500)

# Route to fetch all pending requisitions
@router.get("/pending_request", response_class=HTMLResponse)
async def pending_request(request: Request, db: Session = Depends(script.get_db)):
    
    msg = []
    
    user = utility.get_staff_from_token(request, db)
    admin = utility.get_user_from_token(request, db)


    if not user and not admin:
        msg.append("Session expired, LOGIN required")
        return templates.TemplateResponse(
        "login.html",{
        "request": request,
        "msg": msg,
        })
        
    if user:
    
        pending_requests = db.query(model.Requisition).filter(model.Requisition.status == f"pending with {user.designation}").all()
        length_hint = len(pending_requests)
        return templates.TemplateResponse("pending_request.html",{
            "request": request,
            "msg": msg,
            "user": user,
            "role": user.designation,
            "pending_requests": pending_requests,
            "length_hint": length_hint,
        })
    else:
        
        msg.append("UNAUTHORIZED!, Sign in as a Staff to create a requisition")
        return templates.TemplateResponse(
            "dashboard.html",{
            "request": request,
            "user": admin.get("user"),
            "role": admin.get("role"),
            "msg": msg,
            })

# Route to approve a requisition
@router.post("/approve_requisition")
async def approve_requisition(request: Request, id: int = Form(...), db: Session = Depends(script.get_db)):
    user = utility.get_staff_from_token(request, db)

    if not user:
        return JSONResponse(content={"message": "Session expired, LOGIN required"}, status_code=401)

    requisition = db.query(model.Requisition).filter(model.Requisition.id == id).first()

    if not requisition:
        return JSONResponse(content={"status": "error", "message": "Requisition not found!"}, status_code=404)

    try:
        if user.line_manager == "NULL":
            requisition.status = "Approved"
        else:
            requisition.status = f"pending with {user.line_manager}"
        db.commit()
        return JSONResponse(content={"status": "success", "message": "Requisition approved!"})
    except Exception as e:
        return JSONResponse(content={"status": "error", "message": f"Error approving requisition: {e}"}, status_code=500)

# Route to reject a requisition
@router.post("/reject_requisition")
async def reject_requisition(
    request: Request,
    id: int = Form(...),
    comment: str = Form(...),
    db: Session = Depends(script.get_db)
):
    user = utility.get_staff_from_token(request, db)

    if not user:
        return JSONResponse(content={"message": "Session expired, LOGIN required"}, status_code=401)

    requisition = db.query(model.Requisition).filter(model.Requisition.id == id).first()

    if not requisition:
        return JSONResponse(content={"status": "error", "message": "Requisition not found!"}, status_code=404)

    try:
        requisition.status = "Rejected"
        new_comment = model.RequisitionComment(
            requisition_id=requisition.id,
            comment=comment,
            created_by=user.email
        )
        db.add(new_comment)
        db.commit()
        return JSONResponse(content={"status": "success", "message": "Requisition rejected with comment!"})
    except Exception as e:
        return JSONResponse(content={"status": "error", "message": f"Error rejecting requisition: {e}"}, status_code=500)



# FastAPI route for rendering edit requisition form
@router.get("/edit_requisition/{id}", response_class=HTMLResponse)
async def edit_requisition(
    id: int,
    request: Request,
    db: Session = Depends(script.get_db)
):
    user = utility.get_staff_from_token(request, db)

    if not user:
        return JSONResponse(content={"message": "Session expired, LOGIN required"}, status_code=401)

    requisition = db.query(model.Requisition).filter(model.Requisition.id == id).first()
    if not requisition:
        return JSONResponse(content={"message": "Requisition not found"}, status_code=404)

    return templates.TemplateResponse(
        "edit_request_form.html",
        {
            "request": request,
            "requisition": requisition,
            "msg": [],
            "user": user,
        },
    )

# Route to edit a rejected requisition
@router.post("/edit-requisition", response_class=JSONResponse)
async def edit_requisition(
    request: Request,
    requisition_input: str = Form(...),
    db: Session = Depends(script.get_db)
):
    try:
        # Validate and parse the input using the Pydantic model
        requisition_data = RequisitionInput.parse_raw(requisition_input)
                
    except (json.JSONDecodeError, ValidationError) as e:
        return JSONResponse(content={"message": f"Invalid input: {e}"}, status_code=400)

    user = utility.get_staff_from_token(request, db)

    if not user:
        return JSONResponse(content={"message": "Session expired, LOGIN required"}, status_code=401)

    requisition = db.query(model.Requisition).filter(
        model.Requisition.request_number == requisition_data.request_number,
        model.Requisition.status == "Rejected"
    ).first()

    if not requisition:
        return JSONResponse(content={"status": "error", "message": "Requisition not found or not editable!"}, status_code=404)
    if requisition.status != "Rejected":
        return JSONResponse(content={"status": "error", "message": "requisition not found or not editable!"}, status_code=400)

    try:
        requisition.description = requisition_data.description

        db.query(model.LineItem).filter(
            model.LineItem.requisition_id == requisition.id).delete(synchronize_session=False)
        
        new_line_items = []
        
        for updated_item in requisition_data.line_items:
            new_line_item = model.LineItem(
                item_name=updated_item.item_name,
                quantity=updated_item.quantity,
                category=updated_item.category,
                item_reason=updated_item.item_reason,
                requisition_id=requisition.id
            )
            new_line_items.append(new_line_item)
            
        try:
            for item in new_line_items:
                db.add(item)
                try:
                    db.flush()  #Validate and check constraints for each item
                except Exception as e:
                    return JSONResponse(content={"status": "error", "message": f"Error saving line item: {e}"}, status_code=400)
        except Exception as e:
            return JSONResponse(content={"status": "error", "message": f"Error saving line items: {e}"}, status_code=500)

        requisition.status = f"pending with {user.line_manager}"
        db.commit()
                
    except Exception as e:
        return JSONResponse(content={"message": f"Error creating requisition: {e}"}, status_code=500)

# Route to delete a rejected requisition
@router.post("/delete_requisition")
async def delete_requisition(request: Request, id: int = Form(...), db: Session = Depends(script.get_db)):
    user = utility.get_staff_from_token(request, db)

    if not user:
        return JSONResponse(content={"message": "Session expired, LOGIN required"}, status_code=401)

    requisition = db.query(model.Requisition).filter(
        model.Requisition.id == id,
        model.Requisition.status == "Rejected"
    ).first()

    if not requisition:
        return JSONResponse(content={"status": "error", "message": "Requisition not found or not deletable!"}, status_code=404)

    try:
        db.delete(requisition)
        db.commit()
        return JSONResponse(content={"status": "success", "message": "Requisition deleted successfully!"})
    except Exception as e:
        return JSONResponse(content={"status": "error", "message": f"Error deleting requisition: {e}"}, status_code=500)

# Route to fetch requisition details with comments
@router.get("/requisition_details/{id}", response_class=JSONResponse)
async def requisition_details(id: int, db: Session = Depends(script.get_db)):
    requisition = db.query(model.Requisition).filter(model.Requisition.id == id).first()

    if not requisition:
        return JSONResponse(content={"status": "error", "message": "Requisition not found!"}, status_code=404)

    comments = db.query(model.RequisitionComment).filter(model.RequisitionComment.requisition_id == id).all()

    def serialize_datetime(dt):
        if isinstance(dt, datetime):
            return dt.isoformat()
        return dt

    return JSONResponse(content={
        "status": "success",
        "requisition": {
            "id": requisition.id,
            "request_number": requisition.request_number,
            "description": requisition.description,
            "status": requisition.status,
            "comments": [
                {
                    "comment": c.comment,
                    "created_by": c.created_by,
                    "created_at": serialize_datetime(c.created_at)
                } for c in comments
            ]
        }
    })