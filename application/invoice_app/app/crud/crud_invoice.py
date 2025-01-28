from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload
from app.db.models import Invoice, InvoiceItem
from app.schemas.invoice import InvoiceCreate
from typing import List, Optional
from fastapi import HTTPException
import logging

logger = logging.getLogger(__name__)

async def check_invoice_number_exists(db: AsyncSession, invoice_number: str) -> bool:
    result = await db.execute(
        select(Invoice).filter(Invoice.invoice_number == invoice_number)
    )
    return result.scalar_one_or_none() is not None

from app.db.models.invoice import create_invoice as create_invoice_db

async def create_invoice(db: AsyncSession, invoice_data: InvoiceCreate):
    # Convert AsyncSession to Session since create_invoice_db expects a regular Session
    sync_db = db.sync_session()
    try:
        return await create_invoice_db(db=sync_db, invoice_data=invoice_data)
    finally:
        sync_db.close()

async def get_invoice(db: AsyncSession, invoice_id: int) -> Optional[Invoice]:
    # Update the query to eagerly load both items and client
    result = await db.execute(
        select(Invoice)
        .options(
            selectinload(Invoice.items),
            selectinload(Invoice.client)
        )
        .filter(Invoice.id == invoice_id)
    )
    return result.scalar_one_or_none()

async def get_invoices(db: AsyncSession, skip: int = 0, limit: int = 100) -> List[Invoice]:
    result = await db.execute(
        select(Invoice)
        .options(
            selectinload(Invoice.items),
            selectinload(Invoice.client)
        )
        .offset(skip)
        .limit(limit)
    )
    return result.scalars().all()
