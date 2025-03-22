"""Routes related to User Account creation."""

from fastapi import APIRouter, Depends, Request, Form, status, HTTPException, File, UploadFile
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from database import model, script
from router import user
from services.utility import bcrpyt_context, get_user_from_token
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from config import get_settings
from services import keygen, utility, crud
from datetime import datetime
import json
from pydantic import ValidationError
import os
from schema import schematic



router = APIRouter(prefix="/requisition", tags=["requisition"])

templates = Jinja2Templates(directory="templates")

# Directory to store uploaded files
UPLOAD_DIR = "uploads/"
os.makedirs(UPLOAD_DIR, exist_ok=True)


#new request get route
@router.get("/create-requisition", response_class=HTMLResponse)
async def create_requisition(
    request: Request,
    db:Session=Depends(script.get_db)):
    
    msg = []
    
    requestor = utility.get_staff_from_token(request, db)
    
    if not requestor:
        msg.append("Sign in as a Staff to create a requisition")
        return templates.TemplateResponse("login.html", {
            "request": request, 
            "msg": msg,
        })
        
    reid = str('ReID' + keygen.create_unique_random_key(db))
    
    return templates.TemplateResponse(
        "request_form.html", {
            "request": request, 
            "msg": msg,
            "reid": reid,
            "user": requestor,
            "role": requestor.designation,
        })

#new request post route
@router.post("/create-requisition", response_class = JSONResponse)
async def create_requisition(
    request: Request,
    requisition_input: str = Form(...),
    attachment: UploadFile = File(None),
    db:Session=Depends(script.get_db)
    ):
        
    # Parse the requisition input string into a dictionary
    try:
        requisition_data = json.loads(requisition_input)
        
    except json.JSONDecodeError:
        return JSONResponse(content={"message": "Invalid JSON format in requisition_input"}, status_code=400)
    
    # Convert requisition_data into RequisitionInput
    try:
        requisition_input = schematic.RequisitionInput(**requisition_data)
        
    except ValidationError as e:
        return JSONResponse(content={"message": f"Validation error: {e}"}, status_code=400)
        
    # Save the attachment if it exists
    attachment_path = None
    
    try:
        if attachment:
            try:
                file_location = f"static/uploads/{attachment.filename}"
                os.makedirs(os.path.dirname(file_location), exist_ok=True)
                with open(file_location, "wb") as f:
                    f.write(await attachment.read())
                    attachment_path = file_location
            except Exception as e:
                return JSONResponse(content={"message": f"Error saving attachment: {e}"}, status_code=500)
        
        # Prepare the line items data
        line_items_data = [item.dict() for item in requisition_input.line_items]

        requestor = utility.get_staff_from_token(request, db)

        # Create requisition and line items
        requisition = crud.create_requisition(
            db=db,
            request_number = requisition_input.request_number,
            description = requisition_input.description,
            attachment_path = attachment_path,
            requestor_id = requestor.id,
            status = f"pending with {requestor.line_manager}",
            line_items_data = line_items_data,
        )
        
        # return {"message": "requisition created successfully!"}
        return JSONResponse(content={"message": "Requisition created successfully!"}, status_code=200)
    
        
    except Exception as e:
        # Log the error to help with debugging
        return JSONResponse(content={"message": f"Error creating requisition: {e}"}, status_code=500)

# Route to fetch all pending requisitions
@router.get("/pending_request", response_class=HTMLResponse)
async def pending_request(
    request: Request,
    db:Session=Depends(script.get_db)
    ):
    
    msg = []
    
    user = utility.get_staff_from_token(request, db)

    if not user:
        msg.append("Session expired, LOGIN required")
        return templates.TemplateResponse(
        "login.html",{
        "request": request,
        "msg": msg,
        })
        
    pending_requests = db.query(model.Requisition).filter(model.Requisition.status == f"pending with {user.designation}").all()
    print(f"pending with {user.designation}")
    length_hint = len(pending_requests)
    
    return templates.TemplateResponse(
        "pending_request.html",{
        "request": request,
        "msg": msg,
        "user": user,
        "role": user.designation,
        "pending_requests": pending_requests,
        "length_hint": length_hint
        })


# FastAPI route for approving requisition
@router.post("/approve_requisition")
async def approve_requisition(
    request: Request,
    id: int = Form(...),
    db:Session=Depends(script.get_db)
):
    msg = []
    
    user = utility.get_staff_from_token(request, db)

    if not user:
        msg.append("Session expired, LOGIN required")
        return JSONResponse(content={"message": "Session expired, LOGIN required"}, status_code=401)
    
    requisitions = db.query(model.Requisition).filter(model.Requisition.id == id).first()

    if requisitions:
        requisitions.status = f"pending with {user.line_manager}"
        db.commit()
        return JSONResponse(content={"status": "success", "message": "Requisition approved!"})
    return JSONResponse(content={"status": "error", "message": "Requisition not found!"})


# FastAPI route for rejecting requisition
@router.post("/reject_requisition")
async def reject_requisition(
    request: Request,
    id: int = Form(...),
    db:Session=Depends(script.get_db)
):
    msg = []
    
    user = utility.get_staff_from_token(request, db)

    if not user:
        msg.append("Session expired, LOGIN required")
        return JSONResponse(content={"message": "Session expired, LOGIN required"}, status_code=401)
    
    requisitions = db.query(model.Requisition).filter(model.Requisition.id == id).first()

    if requisitions:
        requisitions.status = "Rejected"
        db.commit()
        return JSONResponse(content={"status": "success", "message": "Requisition rejected!"})
    return JSONResponse(content={"status": "error", "message": "Requisition not found!"})