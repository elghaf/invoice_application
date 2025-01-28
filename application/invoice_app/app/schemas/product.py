from pydantic import BaseModel
from datetime import datetime
from typing import Optional

class ProductBase(BaseModel):
    description: str
    unit: str
    unit_price: float
    category: str

class ProductCreate(ProductBase):
    pass

class ProductUpdate(ProductBase):
    pass

class Product(ProductBase):
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
