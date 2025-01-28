from sqlalchemy.orm import relationship
from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey
from datetime import datetime
from . import Base

class Invoice(Base):
    __tablename__ = "invoices"

    id = Column(Integer, primary_key=True, index=True)
    customer_name = Column(String, index=True)
    amount = Column(Float)
    created_at = Column(DateTime, default=datetime.utcnow)
    status = Column(String, default="pending")
    
    items = relationship("InvoiceItem", back_populates="invoice")

class InvoiceItem(Base):
    __tablename__ = "invoice_items"

    id = Column(Integer, primary_key=True, index=True)
    invoice_id = Column(Integer, ForeignKey("invoices.id"))
    description = Column(String)
    quantity = Column(Integer)
    unit_price = Column(Float)
    total_price = Column(Float)
    
    invoice = relationship("Invoice", back_populates="items")

async def create_invoice(db, **kwargs):
    db_invoice = Invoice(**kwargs)
    db.add(db_invoice)
    await db.commit()
    await db.refresh(db_invoice)
    return db_invoice

__all__ = ["Invoice", "InvoiceItem", "create_invoice"]
