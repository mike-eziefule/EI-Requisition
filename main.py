"""Main FastAPI App."""

from os import link
from fastapi import FastAPI
from router import auth, user, link, requests
from config import get_settings
from fastapi.middleware.cors import CORSMiddleware
from fastapi.templating import Jinja2Templates
from starlette.staticfiles import StaticFiles
from database.script import Base, engine


app = FastAPI(
    title="Requisition api",
    description="A FastAPI-based website.",
    version="0.1.0",
    openapi_tags= get_settings().tags
)

#read metadata, and instructing it to create tables using base schema.
Base.metadata.create_all(bind=engine)

#HTML Dependencies
templates = Jinja2Templates(directory="templates")

#CSS/JS Dependencies
app.mount("/static", StaticFiles(directory="static"), name="static")


# #CORS middleware restrictions
origins = ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins = origins,
    allow_credentials = True,
    allow_methods = ["*"],
    allow_headers = ["*"]
)


# Include the router
app.include_router(link.router)
app.include_router(auth.router)
app.include_router(user.router)
app.include_router(requests.router)
