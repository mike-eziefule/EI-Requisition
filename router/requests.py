"""Routes related to requisitions."""

from fastapi import APIRouter, Depends, Request, Form, status, HTTPException, File, UploadFile
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from database import model, script
from fastapi.responses import HTMLResponse, JSONResponse
from config import get_settings
from services import keygen, utility, crud
from datetime import datetime
import json
from pydantic import ValidationError
import os
from schema.schematic import RequisitionInput
from services.responses import (
    signin_failed_response,
    request_dash_response,
    request_history_response,
    pending_request_response,
    create_requisition_success_response,
    create_requisition_failed_response,
    edit_requisition_failed_response,
    edit_requisition_success_response,
    delete_requisition_success_response,
    delete_requisition_failed_response,
)

router = APIRouter(prefix="/requisition", tags=["requisition"])

templates = Jinja2Templates(directory="templates")

#dashboard page route
@router.get("/request_dash", response_class=HTMLResponse)
async def request_dash(
    request: Request,
    db:Session=Depends(script.get_db)
    ):
    msg = []
    user_data = utility.get_user_from_token(request, db)
    
    if not user_data:
        msg.append("Session expired, LOGIN required")
        return signin_failed_response(request, msg)
    
    if user_data:
        all_requests = db.query(model.Requisition).filter(model.Requisition.requestor_id == user_data.id).all()
        request_length = len(all_requests)
        
        all_users = db.query(model.User).filter(model.User.organization_id == user_data.organization_id).all()
        return request_dash_response(
            request, user_data, all_requests, request_length, all_users
        )
    

#dashboard page route
@router.get("/request_history", response_class=HTMLResponse)
async def request_history(
    request: Request,
    db:Session=Depends(script.get_db)
    ):
    msg = []
    user_data = utility.get_user_from_token(request, db)
    if not user_data:
        msg.append("Session expired, LOGIN required")
        return signin_failed_response(request, msg)
    if user_data:
        all_requests = db.query(model.Requisition).filter(model.Requisition.requestor_id == user_data.id, model.Requisition.status == "Approved" ).all()
        request_length = len(all_requests)
        return request_history_response(
            request, user_data, all_requests, request_length
        )
    

# Route to create a new requisition (GET)
@router.get("/create-requisition", response_class=HTMLResponse)
async def create_requisition(request: Request, db: Session = Depends(script.get_db)):
    
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
        # Generate a unique request number
        reid = str('ReID' + keygen.create_unique_random_key(db))
        
        return templates.TemplateResponse("request_form.html",{
            "request": request,
            "msg": msg,
            "reid": reid,
            "user": user_data,
            "role": user_data.designation}
        )



# Route to create a new requisition (POST)
@router.post("/create-requisition", response_class=JSONResponse)
async def create_requisition(
    request: Request,
    requisition_input: str = Form(...),
    db: Session = Depends(script.get_db)
):  
    try:
        requisition_obj = RequisitionInput.parse_raw(requisition_input)
    except (json.JSONDecodeError, ValidationError) as e:
        print("Validation error:", e)
        return create_requisition_failed_response(e)

    requestor = utility.get_user_from_token(request, db)
    if not requestor:
        return create_requisition_failed_response("Session expired, LOGIN required", status_code=401)
    
    line_manager = utility.get_line_manager(db, requestor)

    try:
        requisition = crud.create_requisition(
            db=db,
            request_number=requisition_obj.request_number,
            description=requisition_obj.description,
            status=f"pending with {line_manager.designation}" if line_manager else "pending with MD/CEO",
            requestor_id=requestor.id,
            line_items_data=requisition_obj.line_items,
        )
        return create_requisition_success_response()
    except Exception as e:
        return create_requisition_failed_response(e)

# Route to fetch all pending requisitions
@router.get("/pending_request", response_class=HTMLResponse)
async def pending_request(request: Request, db: Session = Depends(script.get_db)):
    msg = []
    
    # Fetch user data from the token
    user_data = utility.get_user_from_token(request, db)
    
    # If user data is not found, return a message
    if not user_data:
        msg.append("Session expired, LOGIN required")
        return signin_failed_response(request, msg)
    
    # Fetch all pending requisitions for the user
    if user_data:
        # pending_requests = db.query(model.Requisition).filter(model.Requisition.status == f"pending with {user_data.designation}", model.Requisition.requestor['organization_id'] == user_data.organization_id).all()
        pending_requests = (db.query(model.Requisition).
            join(model.Requisition.requestor).filter(
            model.Requisition.status == f"pending with {user_data.designation}",
            model.User.organization_id == user_data.organization_id).all()
        )
        
        length_hint = len(pending_requests)
        all_users = db.query(model.User).filter(model.User.organization_name == user_data.organization_name).all()
        
        # Return the pending requests response
        return pending_request_response(
            request, user_data, pending_requests, length_hint, all_users, msg
        )
    

# Route to approve a requisition
@router.post("/approve_requisition")
async def approve_requisition(request: Request, id: int = Form(...), db: Session = Depends(script.get_db)):
    user_data = utility.get_user_from_token(request, db)
    if not user_data:
        return JSONResponse(content={"message": "Session expired, LOGIN required"}, status_code=401)

    user_cmd_level = int(user_data.cmd_level)
    line_manager = None

    # Try to find a line manager in the same department, one level lower at a time
    for level in range(user_cmd_level - 1, 0, -1):
        line_manager = db.query(model.User).filter(
            model.User.department == user_data.department,
            model.User.cmd_level == str(level).zfill(3)
        ).first()
        if line_manager:
            break

    # Fallback: search for any user with the required command level
    if not line_manager:
        for level in range(user_cmd_level - 1, 0, -1):
            line_manager = db.query(model.User).filter(
                model.User.cmd_level == str(level).zfill(3)
            ).first()
            if line_manager:
                break

    requisition = db.query(model.Requisition).filter(model.Requisition.id == id).first()
    if not requisition:
        return JSONResponse(content={"status": "error", "message": "Requisition not found!"}, status_code=404)

    try:
        if user_data.cmd_level == "001":
            requisition.status = "Approved"
        else:
            requisition.status = f"pending with {line_manager.designation}" if line_manager else "pending with MD/CEO"
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
    user_data = utility.get_user_from_token(request, db)

    if not user_data:
        return JSONResponse(content={"message": "Session expired, LOGIN required"}, status_code=401)

    requisition = db.query(model.Requisition).filter(model.Requisition.id == id).first()

    if not requisition:
        return JSONResponse(content={"status": "error", "message": "Requisition not found!"}, status_code=404)

    try:
        requisition.status = "Rejected"
        new_comment = model.RequisitionComment(
            requisition_id=requisition.id,
            comment=comment,
            created_by=user_data.email
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
    user_data = utility.get_user_from_token(request, db)

    if not user_data:
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
            "user": user_data,
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
        requisition_data = RequisitionInput.parse_raw(requisition_input)
    except (json.JSONDecodeError, ValidationError) as e:
        return edit_requisition_failed_response(e)

    user_data = utility.get_user_from_token(request, db)

    if not user_data:
        return edit_requisition_failed_response("Session expired, LOGIN required", status_code=401)

    requisition = db.query(model.Requisition).filter(
        model.Requisition.request_number == requisition_data.request_number,
        model.Requisition.status == "Rejected"
    ).first()

    if not requisition or requisition.status != "Rejected":
        return edit_requisition_failed_response("Requisition not found or not editable!", status_code=404)
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


        line_manager = db.query(model.User).filter(
        model.User.department == user_data.department,
        model.User.cmd_level == (int(user_data.cmd_level) - 1)
        ).first()
    
        if not line_manager:
            line_manager = db.query(model.User).filter(model.User.cmd_level == (str(user_data.cmd_level) - 1))  # If no line manager found, set to None
    


        requisition.status = f"pending with {line_manager.designation}"
        db.commit()
                
    except Exception as e:
        return edit_requisition_failed_response(e)

# Route to delete a rejected requisition
@router.post("/delete_requisition")
async def delete_requisition(request: Request, id: int = Form(...), db: Session = Depends(script.get_db)):
    user_data = utility.get_user_from_token(request, db)

    if not user_data:
        return delete_requisition_failed_response("Session expired, LOGIN required", status_code=401)

    requisition = db.query(model.Requisition).filter(
        model.Requisition.id == id,
        model.Requisition.status == "Rejected"
    ).first()

    if not requisition:
        return delete_requisition_failed_response("Requisition not found or not deletable!", status_code=404)

    try:
        db.delete(requisition)
        db.commit()
        return delete_requisition_success_response()
    except Exception as e:
        return delete_requisition_failed_response(e)

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