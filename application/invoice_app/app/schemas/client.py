from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import datetime

class ClientBase(BaseModel):
    name: str
    phone: str
    email: Optional[EmailStr] = None
    address: Optional[str] = None

class ClientCreate(ClientBase):
    pass

class ClientUpdate(ClientBase):
    pass

class Client(ClientBase):
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True