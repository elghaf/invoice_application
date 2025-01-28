from pydantic import BaseModel, computed_field
from typing import List, Optional
from datetime import datetime

class InvoiceItemCreate(BaseModel):
    description: str
    unit: str
    quantity: int
    length: float
    unit_price: float
    
    @computed_field
    def total_price(self) -> float:
        return self.quantity * self.length * self.unit_price

class InvoiceCreate(BaseModel):
    invoice_number: str
    date: Optional[datetime] = None
    project: str
    client_name: str
    client_phone: str
    address: str
    total_ht: float
    tax: float
    total_ttc: float
    frame_number: Optional[str] = None
    items: List[InvoiceItemCreate]
    
    @computed_field
    def customer_name(self) -> str:
        return self.client_name
    
    @computed_field
    def amount(self) -> float:
        return self.total_ttc

class InvoiceItemResponse(InvoiceItemCreate):
    id: int
    invoice_id: int

    class Config:
        from_attributes = True

class InvoiceResponse(InvoiceCreate):
    id: int
    items: List[InvoiceItemResponse]

    class Config:
        from_attributes = True 