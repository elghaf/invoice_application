from sqlalchemy.orm import Session
from app.models import database as models
from app.schemas import invoice as schemas
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

def create_invoice_item(db: Session, item_data: dict, invoice_id: int):
    logger.info(f"Creating invoice item with data: {item_data}")
    try:
        # Access dictionary values directly
        db_item = models.InvoiceItem(
            invoice_id=invoice_id,
            description=item_data['description'],
            unit=item_data['unit'],
            quantity=item_data['quantity'],
            unit_price=item_data['unit_price'],
            length=item_data.get('length', 0.0)
        )
        db.add(db_item)
        return db_item
    except KeyError as e:
        logger.error(f"Missing key in item data: {e}")
        raise ValueError(f"Missing required field in item: {e}")
    except Exception as e:
        logger.error(f"Error creating invoice item: {str(e)}")
        raise

def create_invoice(db: Session, invoice_data: schemas.InvoiceCreate):
    logger.info(f"Creating invoice with data: {invoice_data.model_dump()}")  # Use model_dump() instead of dict()
    try:
        # Create invoice
        db_invoice = models.Invoice(
            invoice_number=invoice_data.invoice_number,
            date=invoice_data.date,
            project=invoice_data.project,
            total_ht=invoice_data.total_ht,
            tax=invoice_data.tax,
            total_ttc=invoice_data.total_ttc,
            client_name=invoice_data.client_name,
            client_phone=invoice_data.client_phone,
            frame_number=invoice_data.frame_number,
            client_id=invoice_data.client_id,
            status='draft'  # Add default status
        )
        db.add(db_invoice)
        db.flush()

        # Create invoice items
        logger.info(f"Processing items: {invoice_data.items}")
        for item_data in invoice_data.items:
            if not isinstance(item_data, dict):
                item_data = item_data.dict()
            create_invoice_item(db, item_data, db_invoice.id)

        db.commit()
        db.refresh(db_invoice)
        return db_invoice
    except Exception as e:
        logger.error(f"Error creating invoice: {str(e)}")
        db.rollback()
        raise ValueError(f"Error creating invoice: {str(e)}") 