from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse

templates = Jinja2Templates(directory="templates")

def registration_failed_response(
    request, msg, organization_name, rc_number, address, owner_name,
    owner_designation, email, owner_password, password2, owner_role, product
):
    return templates.TemplateResponse("register.html", {
        "request": request, 
        "msg": msg,
        "organization_name": organization_name,  
        "rc_number": rc_number,
        "address": address,
        "owner_name": owner_name,
        "owner_designation": owner_designation,
        "email": email,
        "owner_password": owner_password,
        "password2": password2,
        "owner_role": owner_role,
        "product": product
    })

def registration_success_response(request, msg):
    return templates.TemplateResponse("signin.html", {
        "request": request, 
        "msg": msg,
    })

def add_member_failed_response(
    request, msg, staff_name, designation, cmd_level, role, email, password, password2, user, department
):
    return templates.TemplateResponse("add_member.html", {
        "request": request, 
        "msg": msg,
        "staff_name": staff_name,
        "designation": designation,
        "cmd_level": cmd_level,
        "role": role,
        'email': email,
        'password': password,
        'password2': password2,
        "user": user,
        "role": user.designation,
        "department": department   
    })

def add_member_success_response(request, msg, user, staff_number, all_users, user_line_managers):
    return templates.TemplateResponse(
        "viewstaff.html",{
        "request": request,
        "msg":msg,
        "user": user,
        "role": user.designation,
        "all_users": all_users,
        "staff_number": staff_number,
        "user_line_managers": user_line_managers,
    })

def signin_failed_response(request, msg):
    from fastapi.templating import Jinja2Templates
    templates = Jinja2Templates(directory="templates")
    return templates.TemplateResponse("signin.html", {
        "request": request,
        "msg": msg,
    })

def request_dash_response(request, user_data, all_requests, request_length, all_users):
    from fastapi.templating import Jinja2Templates
    templates = Jinja2Templates(directory="templates")
    return templates.TemplateResponse("request_dash.html", {
        "request": request,
        "user": user_data,
        "role": user_data.designation,
        "all_requests": all_requests,
        "request_length": request_length,
        "all_users": all_users
    })

def request_history_response(request, user_data, all_requests, request_length):
    from fastapi.templating import Jinja2Templates
    templates = Jinja2Templates(directory="templates")
    return templates.TemplateResponse("request_dash.html", {
        "request": request,
        "user": user_data,
        "role": user_data.designation,
        "all_requests": all_requests,
        "request_length": request_length,
    })

def pending_request_response(request, user_data, pending_requests, length_hint, all_users, msg):
    from fastapi.templating import Jinja2Templates
    templates = Jinja2Templates(directory="templates")
    return templates.TemplateResponse("pending_request.html", {
        "request": request,
        "msg": msg,
        "user": user_data,
        "role": user_data.designation,
        "pending_requests": pending_requests,
        "length_hint": length_hint,
        "all_users": all_users
    })

def create_requisition_success_response():
    from fastapi.responses import JSONResponse
    return JSONResponse(content={"message": "Requisition created successfully!"}, status_code=200)

def create_requisition_failed_response(error, status_code=400):
    from fastapi.responses import JSONResponse
    return JSONResponse(content={"message": f"Invalid input: {error}"}, status_code=status_code)

def edit_requisition_success_response():
    from fastapi.responses import JSONResponse
    return JSONResponse(content={"message": "Requisition edited successfully!"}, status_code=200)

def edit_requisition_failed_response(error, status_code=400):
    from fastapi.responses import JSONResponse
    return JSONResponse(content={"message": f"Error editing requisition: {error}"}, status_code=status_code)

def delete_requisition_success_response():
    from fastapi.responses import JSONResponse
    return JSONResponse(content={"status": "success", "message": "Requisition deleted successfully!"})

def delete_requisition_failed_response(error, status_code=400):
    from fastapi.responses import JSONResponse
    return JSONResponse(content={"status": "error", "message": f"{error}"}, status_code=status_code)

def expense_dash_response(request, user_data, expenses, expense_length, all_users):
    from fastapi.templating import Jinja2Templates
    templates = Jinja2Templates(directory="templates")
    return templates.TemplateResponse("expense_dash.html", {
        "request": request,
        "user": user_data,
        "role": user_data.designation,
        "expenses": expenses,
        "expense_length": expense_length,
        "all_users": all_users
    })

def pending_expense_response(request, user_data, pending_expenses, length_hint, all_users, msg):
    from fastapi.templating import Jinja2Templates
    templates = Jinja2Templates(directory="templates")
    return templates.TemplateResponse("pending_expense.html", {
        "request": request,
        "msg": msg,
        "user": user_data,
        "role": user_data.designation,
        "pending_expenses": pending_expenses,
        "length_hint": length_hint,
        "all_users": all_users
    })

def create_expense_success_response():
    from fastapi.responses import JSONResponse
    return JSONResponse(content={"message": "Expense created successfully!"}, status_code=200)

def create_expense_failed_response(error, status_code=400):
    from fastapi.responses import JSONResponse
    return JSONResponse(content={"message": f"Invalid input: {error}"}, status_code=status_code)
