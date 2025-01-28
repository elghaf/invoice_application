from sqlalchemy.orm import DeclarativeBase, relationship
from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey
from datetime import datetime

class Base(DeclarativeBase):
    pass

class Invoice(Base):
    __tablename__ = "invoices"

    id = Column(Integer, primary_key=True, index=True)
    customer_name = Column(String, index=True)
    amount = Column(Float)
    created_at = Column(DateTime, default=datetime.utcnow)
    status = Column(String, default="pending")
    
    # Add relationship to InvoiceItem
    items = relationship("InvoiceItem", back_populates="invoice")

class InvoiceItem(Base):
    __tablename__ = "invoice_items"

    id = Column(Integer, primary_key=True, index=True)
    invoice_id = Column(Integer, ForeignKey("invoices.id"))
    description = Column(String)
    quantity = Column(Integer)
    unit_price = Column(Float)
    total_price = Column(Float)
    
    # Add relationship to Invoice
    invoice = relationship("Invoice", back_populates="items")

__all__ = ["Base", "Invoice", "InvoiceItem"]
