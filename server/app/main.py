import os
from fastapi import FastAPI, HTTPException, Request, Form, Depends
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles

app = FastAPI()

templates = Jinja2Templates(
    directory=os.path.join(os.path.dirname(os.path.abspath(__file__)), "templates")
)

app.mount("/static", StaticFiles(directory="server/app/static"), name="static")
app.mount("/reports", StaticFiles(directory="server/app/reports"), name="reports")
