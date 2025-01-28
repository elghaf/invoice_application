from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from fastapi.templating import Jinja2Templates
from app.api.endpoints import invoices
from app.core.config import settings
from app.db.database import init_db

app = FastAPI(title=settings.PROJECT_NAME)

# Mount static files with correct path
app.mount("/static", StaticFiles(directory="app/static"), name="static")

# Templates with correct path
templates = Jinja2Templates(directory="app/templates")

# Include routers
app.include_router(invoices.router, prefix="/api/invoices", tags=["invoices"])

@app.on_event("startup")
async def startup_event():
    await init_db()

@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})