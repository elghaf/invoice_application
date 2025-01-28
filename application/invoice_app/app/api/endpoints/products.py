from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.database import get_db
from app.db.models import Product
from app.schemas.product import Product as ProductSchema
from sqlalchemy import select
from typing import List

router = APIRouter()

@router.get("/categories/{category}", response_model=List[ProductSchema])
async def get_products_by_category(
    category: str,
    db: AsyncSession = Depends(get_db)
):
    """Get products by category (POUTRELLES, HOURDIS, PANNEAU)"""
    query = select(Product).filter(Product.category == category.upper())
    result = await db.execute(query)
    products = result.scalars().all()
    return products

@router.get("/", response_model=List[ProductSchema])
async def get_all_products(
    db: AsyncSession = Depends(get_db)
):
    """Get all products"""
    query = select(Product)
    result = await db.execute(query)
    products = result.scalars().all()
    return products

@router.post("/", response_model=ProductSchema)
async def create_product(
    product: ProductSchema,
    db: AsyncSession = Depends(get_db)
):
    """Create a new product"""
    db_product = Product(**product.dict())
    db.add(db_product)
    await db.commit()
    await db.refresh(db_product)
    return db_product