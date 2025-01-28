
from sqlalchemy.orm import DeclarativeBase

class Base(DeclarativeBase):
    pass

from .invoice import Invoice, InvoiceItem

__all__ = ["Base", "Invoice", "InvoiceItem"]