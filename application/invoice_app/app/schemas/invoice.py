from pydantic import BaseModel, validator, Field, ConfigDict
from typing import List, Optional, Dict, Any
from datetime import datetime

class InvoiceItemBase(BaseModel):
    description: str
    quantity: int
    unit_price: float
    total_price: float

class InvoiceItemCreate(InvoiceItemBase):
    pass

class InvoiceItemResponse(InvoiceItemBase):
    id: int
    invoice_id: int

    class Config:
        from_attributes = True

class InvoiceBase(BaseModel):
    customer_name: str
    amount: float
    status: str = "pending"

class InvoiceCreate(InvoiceBase):
    items: List[InvoiceItemCreate]

class InvoiceResponse(InvoiceBase):
    id: int
    created_at: datetime
    items: List[InvoiceItemResponse] = []

    class Config:
        from_attributes = True