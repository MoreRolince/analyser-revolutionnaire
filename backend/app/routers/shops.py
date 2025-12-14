from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from app.database import get_db
from app.models import Shop
from app.schemas import ShopResponse
from app.auth import get_current_active_user

router = APIRouter()

@router.get("", response_model=List[ShopResponse])
async def get_shops(
    skip: int = 0,
    limit: int = 100,
    current_user = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    shops = db.query(Shop).offset(skip).limit(limit).all()
    return shops

@router.get("/{shop_id}", response_model=ShopResponse)
async def get_shop(
    shop_id: int,
    current_user = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    shop = db.query(Shop).filter(Shop.id == shop_id).first()
    if not shop:
        raise HTTPException(status_code=404, detail="Shop not found")
    return shop

