from fastapi import APIRouter, Depends, HTTPException, status, Request, Body, Form
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.database import get_db
from app.schemas.invoice import InvoiceCreate, InvoiceResponse
from app.crud.crud_invoice import create_invoice, get_invoice, get_invoices
from app.services.invoice_service import InvoiceService
from fastapi.responses import StreamingResponse, JSONResponse, HTMLResponse
from typing import List, Dict, Any
from io import BytesIO
import logging
from fastapi.templating import Jinja2Templates
from app.db.models import Invoice as InvoiceModel
from pydantic import ValidationError
import json

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

router = APIRouter()
templates = Jinja2Templates(directory="templates")

@router.post("/", response_model=InvoiceResponse)
async def create_new_invoice(
    invoice: InvoiceCreate,
    db: AsyncSession = Depends(get_db)
):
    # Log the incoming data
    logger.info(f"Received invoice data: {invoice.model_dump()}")
    try:
        return await create_invoice(db=db, invoice_data=invoice)
    except Exception as e:
        logger.error(f"Error creating invoice: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Error creating invoice: {str(e)}"
        )

@router.post("/{invoice_id}/generate-pdf")
async def generate_invoice_pdf(
    invoice_id: int,
    request: Request,
    invoice_data: InvoiceModel
):
    try:
        logger.info(f"Received invoice data: {invoice_data.model_dump()}")
        
        # Generate PDF
        pdf_bytes = InvoiceService.generate_pdf(invoice_data)
        
        return StreamingResponse(
            iter([pdf_bytes]),
            media_type="application/pdf",
            headers={"Content-Disposition": f"attachment; filename=devis_{invoice_id}.pdf"}
        )
    except Exception as e:
        logger.error(f"Error processing request: {str(e)}", exc_info=True)
        if isinstance(e, HTTPException):
            raise e
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{invoice_id}", response_model=InvoiceResponse)
async def read_invoice(
    invoice_id: int,
    db: AsyncSession = Depends(get_db)
):
    invoice = await get_invoice(db=db, invoice_id=invoice_id)
    if invoice is None:
        raise HTTPException(status_code=404, detail="Invoice not found")
    return invoice

@router.get("/", response_model=List[InvoiceResponse])
async def read_invoices(
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_db)
):
    invoices = await get_invoices(db=db, skip=skip, limit=limit)
    return invoices

@router.get("/", response_class=HTMLResponse)
async def serve_html(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@router.post("/generate-invoice")
async def generate_invoice(data: InvoiceModel):
    pdf_bytes = InvoiceService.generate_pdf(data)
    return StreamingResponse(
        iter([pdf_bytes]),
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename=devis.pdf"}
    )