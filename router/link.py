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

#dashboard page route
@router.get("/admin_dash", response_class=HTMLResponse)
async def admin_dash(
    request: Request,
    db:Session=Depends(script.get_db)
    ):
    
    msg = []
    
    user_data = utility.get_user_from_token(request, db)
    
    if not user_data:
        msg.append("Session expired, LOGIN required")
        return templates.TemplateResponse(
        "login.html",{
        "request": request,
        "msg": msg,
        })
        
    if user_data["role"] != "administrator":
        return templates.TemplateResponse(
        "dash.html",{
        "request": request,
        "user": user_data["user"],
        "role": user_data["role"]
        })
    
    return templates.TemplateResponse(
        "dash.html",{
        "request": request,
        "user": user_data.get("user"),
        "role": user_data.get("role")
        })
    
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
        "login.html",{
        "request": request,
        "msg": msg,
        })
        
    if user_data["role"] != "administrator":
        
        msg.append("Contact your administrator")
        return templates.TemplateResponse(
        "dash.html",{
        "request": request,
        "msg": msg,
        "user": user_data["user"],
        "role": user_data["role"]
        })
        
    all_users = db.query(model.User).filter(model.User.organization_id == user_data["user"].id ).all()
    staff_number = len(all_users)
    
    
    return templates.TemplateResponse(
        "viewstaff.html",{
        "request": request,
        "msg":msg,
        "user": user_data.get("user"),
        "role": user_data.get("role"),
        "all_users": all_users,
        "staff_number": staff_number
        })

#shop page
# @router.get("/shop", response_class = HTMLResponse)
# async def shop(
#     request:Request,
#     db:Session=Depends(script.get_db)
# ):
#     """View products."""
#     products = db.query(model.Products).all()
    
    
#     return templates.TemplateResponse(
#         "shop.html", {
#             "request": request,
#             "products": products})


# #checkout page
# @router.get("/checkout", response_class = HTMLResponse)
# async def checkout(
#     request:Request,
# ):
#     return templates.TemplateResponse("checkout.html", {"request": request})


# #cart page
# @router.get("/cart", response_class = HTMLResponse)
# async def cart(
#     request:Request,
# ):
#     return templates.TemplateResponse("cart.html", {"request": request})


# #detail page
# @router.get("/detail/{product_id}", response_class = HTMLResponse)
# async def detail(
#     request:Request, 
#     product_id:int,
#     db:Session=Depends(script.get_db)
# ):
#     msg = []
    
#     """get product detail"""
    
#     result = db.query(model.Products).filter(model.Products.id == product_id).first()
    
#     return templates.TemplateResponse("detail.html", {"request": request, "result": result, "msg": msg})


# #contact page
# @router.get("/contact", response_class = HTMLResponse)
# async def contact(
#     request:Request,
# ):
#     return templates.TemplateResponse("contact.html", {"request": request})

# #add product page
# @router.get("/addproducts", response_class = HTMLResponse)
# async def addproducts(
#     request:Request, db:Session=Depends(script.get_db)
# ):
#     msg = []
    
#     # authentication
#     user = utility.get_user_from_token(request, db)
    
#     if not user:
#         msg.append("Please Sign in to add products")
#         return templates.TemplateResponse("login.html", {"request": request, "msg": msg})
    
    
#     return templates.TemplateResponse("addproducts.html", {"request": request})

# #add product page
# @router.post("/addproducts", response_class = HTMLResponse)
# async def addproducts(
#     request:Request,
#     name: str = Form(...),
#     category: str = Form(...),
#     description: str = Form(...),
#     colour: str = Form(...),
#     brand: str = Form(...),
#     quantity: str = Form(...),
#     price: str = Form(...),
#     image1: str = Form(...),
#     image2: str = Form(...),
#     image3: str = Form(...),
#     db:Session=Depends(script.get_db)
# ):
    
#     msg = []
    
#     # authentication
#     user = utility.get_user_from_token(request, db)
    
#     if not user:
#         msg.append("Session Expired, Login")
#         return templates.TemplateResponse("login.html", {"request": request, "msg": msg})
    
#     #database dump
#     addproduct = model.Products(
#     name = name,
#     category= category,
#     description = description,
#     colour = colour, 
#     brand = brand,
#     quantity = quantity,
#     price = price,
#     image1 = image1,
#     image2 = image2,
#     image3 = image3,
#     )
#     db.add(addproduct)
#     db.commit()
#     db.refresh(addproduct)
    
#     msg.append("Product added successfully")

#     return templates.TemplateResponse("addproducts.html", {"request": request, "msg": msg})
