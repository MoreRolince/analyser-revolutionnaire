from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import List

from app.database import get_db
from app.models import Product
from app.schemas import ProductResponse
from app.auth import get_current_active_user

router = APIRouter()

@router.get("", response_model=List[ProductResponse])
async def get_products(
    skip: int = 0,
    limit: int = 100,
    current_user = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    products = db.query(Product).offset(skip).limit(limit).all()
    return products

@router.get("/trending", response_model=List[ProductResponse])
async def get_trending_products(
    limit: int = 10,
    current_user = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    products = db.query(Product).order_by(Product.score.desc()).limit(limit).all()
    return products

