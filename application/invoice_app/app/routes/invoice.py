from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import Optional
from ..database import get_db
from ..models.invoice import Invoice, ClientType

router = APIRouter()

@router.get("/api/invoices/next-number/{client_type}")
async def get_next_invoice_number(client_type: str, db: Session = Depends(get_db)):
    if client_type not in ClientType.__members__:
        raise HTTPException(status_code=400, detail="Invalid client type")
    
    # Get the last invoice number for this client type
    last_invoice = db.query(Invoice)\
        .filter(Invoice.client_type == ClientType[client_type])\
        .order_by(Invoice.id.desc())\
        .first()
    
    if last_invoice:
        # Extract the number from the last invoice number (DCP/TYPE/NUMBER)
        try:
            last_number = int(last_invoice.invoice_number.split('/')[-1])
            next_number = last_number + 1
        except (ValueError, IndexError):
            next_number = 1
    else:
        next_number = 1
    
    return {"next_number": f"{next_number:04d}"}  # Format as 4 digits

@router.post("/api/invoices/")
async def create_invoice(invoice_data: InvoiceCreate, db: Session = Depends(get_db)):
    # Extract client type from invoice number
    try:
        client_type = invoice_data.invoice_number.split('/')[1]
        if client_type not in ClientType.__members__:
            raise HTTPException(status_code=400, detail="Invalid client type in invoice number")
    except IndexError:
        raise HTTPException(status_code=400, detail="Invalid invoice number format")

    db_invoice = Invoice(
        client_type=ClientType[client_type],
        **invoice_data.dict()
    )
    # ... rest of your existing create logic ... 