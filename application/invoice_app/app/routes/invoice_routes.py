from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse, StreamingResponse
from fastapi.templating import Jinja2Templates
from app.models.invoice import InvoiceData
from app.services.invoice_service import InvoiceService

router = APIRouter()
templates = Jinja2Templates(directory="templates")

@router.get("/", response_class=HTMLResponse)
async def serve_html(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@router.post("/generate-invoice")
async def generate_invoice(data: InvoiceData):
    pdf_bytes = InvoiceService.generate_pdf(data)
    return StreamingResponse(
        iter([pdf_bytes]),
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename=devis.pdf"}
    ) 