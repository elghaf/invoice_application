from sqlalchemy import Column, Integer, String, DateTime, Float, ForeignKey, Sequence
from sqlalchemy.orm import relationship
from ..database import Base

class Invoice(Base):
    __tablename__ = "invoices"
    
    id = Column(Integer, Sequence('invoice_id_seq'), primary_key=True)
    invoice_number = Column(String, unique=True)
    # ... rest of your columns ... 