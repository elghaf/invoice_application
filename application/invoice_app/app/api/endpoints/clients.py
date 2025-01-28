from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.database import get_db
from app.db.models import Client
from app.schemas.client import ClientCreate, Client as ClientSchema
from sqlalchemy import select
from typing import List
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

router = APIRouter()

@router.post("/", response_model=ClientSchema)
async def create_client(
    client: ClientCreate,
    db: AsyncSession = Depends(get_db)
):
    logger.info(f"Creating client: {client.dict()}")
    try:
        db_client = Client(
            name="Default Client",  # Add a default client for testing
            phone="123456789",
            email="ay.elghafraoui@gmail.com",
            address="Default Address"
        )
        db.add(db_client)
        await db.commit()
        await db.refresh(db_client)
        logger.info(f"Created client with ID: {db_client.id}")
        return db_client
    except Exception as e:
        logger.error(f"Error creating client: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/{client_id}", response_model=ClientSchema)
async def read_client(
    client_id: int,
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(select(Client).filter(Client.id == client_id))
    client = result.scalar_one_or_none()
    if client is None:
        raise HTTPException(status_code=404, detail="Client not found")
    return client

@router.get("/", response_model=List[ClientSchema])
async def read_clients(
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(select(Client).offset(skip).limit(limit))
    clients = result.scalars().all()
    return clients
