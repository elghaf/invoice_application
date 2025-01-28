from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from app.routes.invoices import router as invoice_router
from app.db.database import init_db
import os

# Get the absolute path to the app directory
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

app = FastAPI(title="Invoice Generator")

# Mount static files with absolute path
app.mount("/static", StaticFiles(directory=os.path.join(BASE_DIR, "app/static")), name="static")

# Templates with absolute path
templates = Jinja2Templates(directory=os.path.join(BASE_DIR, "app/templates"))

# Include routers
app.include_router(invoice_router, prefix="/api/invoices", tags=["invoices"])

@app.on_event("startup")
async def startup_event():
    await init_db()

# Root endpoint to serve the HTML page
@app.get("/")
async def root(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})