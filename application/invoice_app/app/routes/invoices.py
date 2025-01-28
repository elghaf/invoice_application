from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, Sequence
from typing import List, Optional
from sqlalchemy.orm import selectinload, joinedload, Session
from fastapi.responses import StreamingResponse
import logging
from datetime import datetime

from app.db.database import get_db
from app.schemas.invoice import InvoiceCreate, InvoiceResponse
from app.db.models import Invoice, InvoiceItem
from app.services.invoice_service import InvoiceService

# Set up logging
logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/invoices", tags=["invoices"])

@router.post("/", response_model=InvoiceResponse)
async def create_new_invoice(
    invoice: InvoiceCreate,
    db: AsyncSession = Depends(get_db)
):
    try:
        # Get current max ID
        query = select(func.max(Invoice.id))
        result = await db.execute(query)
        current_max_id = result.scalar() or 0
        next_id = current_max_id + 1
        
        # Extract client type from the invoice number
        client_type = invoice.invoice_number.split('/')[1]
        
        # Create new invoice number
        new_invoice_number = f"DCP/{client_type}/{next_id:04d}"
        
        # Create invoice with the new number
        db_invoice = Invoice(
            id=next_id,
            invoice_number=new_invoice_number,
            date=invoice.date,
            project=invoice.project,
            client_name=invoice.client_name,
            client_phone=invoice.client_phone,
            address=invoice.address,
            total_ht=invoice.total_ht,
            tax=invoice.tax,
            total_ttc=invoice.total_ttc,
            frame_number=invoice.frame_number
        )
        
        db.add(db_invoice)
        await db.commit()
        await db.refresh(db_invoice)
        
        # Create invoice items
        for item_data in invoice.items:
            db_item = InvoiceItem(
                invoice_id=db_invoice.id,
                description=item_data.description,
                unit=item_data.unit,
                quantity=item_data.quantity,
                length=item_data.length,
                unit_price=item_data.unit_price,
                total_price=item_data.total_price
            )
            db.add(db_item)

        await db.commit()
        await db.refresh(db_invoice)
        
        # Explicitly load the items relationship
        result = await db.execute(
            select(Invoice)
            .options(selectinload(Invoice.items))
            .filter(Invoice.id == db_invoice.id)
        )
        return result.scalar_one()

    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{invoice_id}", response_model=InvoiceResponse)
async def read_invoice(invoice_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Invoice)
        .options(selectinload(Invoice.items))
        .filter(Invoice.id == invoice_id)
    )
    invoice = result.scalar_one_or_none()
    if invoice is None:
        raise HTTPException(status_code=404, detail="Invoice not found")
    return invoice

@router.get("/", response_model=List[InvoiceResponse])
async def read_invoices(
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(
        select(Invoice)
        .options(selectinload(Invoice.items))
        .offset(skip)
        .limit(limit)
    )
    return result.scalars().all()

@router.post("/{invoice_id}/generate-pdf")
async def generate_invoice_pdf(
    invoice_id: int,
    request: Request,
    db: AsyncSession = Depends(get_db)
):
    try:
        # Get invoice with items
        result = await db.execute(
            select(Invoice)
            .options(selectinload(Invoice.items))
            .filter(Invoice.id == invoice_id)
        )
        invoice = result.scalar_one_or_none()
        
        if not invoice:
            raise HTTPException(status_code=404, detail="Invoice not found")
            
        logger.info(f"Generating PDF for invoice: {invoice_id}")
        
        # Generate PDF
        pdf_bytes = InvoiceService.generate_pdf(invoice)
        
        return StreamingResponse(
            iter([pdf_bytes]),
            media_type="application/pdf",
            headers={"Content-Disposition": f"attachment; filename=devis_{invoice_id}.pdf"}
        )
    except Exception as e:
        logger.error(f"Error generating PDF: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/last-number/{client_type}", response_model=dict)
async def get_last_invoice_number(
    client_type: str,
    db: AsyncSession = Depends(get_db)
):
    try:
        # Use async query syntax
        query = select(func.max(Invoice.id))
        result = await db.execute(query)
        current_max_id = result.scalar() or 0
        
        # Next ID will be current max + 1
        next_id = current_max_id + 1
        
        # Format the invoice number with the next ID
        formatted_number = f"DCP/{client_type}/{next_id:04d}"
        
        return {
            "next_number": next_id,
            "formatted_number": formatted_number
        }
    except Exception as e:
        print(f"Error in get_last_invoice_number: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/reset-sequence")
def reset_invoice_sequence(db: Session = Depends(get_db)):
    try:
        # Reset the sequence to 1
        db.execute("ALTER SEQUENCE invoice_id_seq RESTART WITH 1")
        db.commit()
        return {"message": "Sequence reset successfully"}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e)) 