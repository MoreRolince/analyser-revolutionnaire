from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from app.database import get_db
from app.models import User, TrackedShop, Shop
from app.schemas import ShopResponse
from app.auth import get_current_active_user

router = APIRouter()

@router.post("/shops/{shop_id}")
async def add_tracked_shop(
    shop_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    # Vérifier les quotas
    tracked_count = db.query(TrackedShop).filter(
        TrackedShop.user_id == current_user.id
    ).count()
    
    max_tracked = 10 if current_user.plan == "3months" else (30 if current_user.plan == "6months" else 3)
    
    if tracked_count >= max_tracked:
        raise HTTPException(
            status_code=403,
            detail="Quota de boutiques suivies atteint"
        )
    
    # Vérifier si déjà suivi
    existing = db.query(TrackedShop).filter(
        TrackedShop.user_id == current_user.id,
        TrackedShop.shop_id == shop_id
    ).first()
    
    if existing:
        raise HTTPException(status_code=400, detail="Shop already tracked")
    
    tracked_shop = TrackedShop(
        user_id=current_user.id,
        shop_id=shop_id,
        alerts_enabled=True
    )
    db.add(tracked_shop)
    db.commit()
    
    return {"message": "Shop added to favorites"}

@router.get("/shops", response_model=List[ShopResponse])
async def get_tracked_shops(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    tracked_shops = db.query(TrackedShop).filter(
        TrackedShop.user_id == current_user.id
    ).all()
    
    shops = [db.query(Shop).filter(Shop.id == ts.shop_id).first() for ts in tracked_shops]
    return [s for s in shops if s]

@router.delete("/shops/{shop_id}")
async def remove_tracked_shop(
    shop_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    tracked_shop = db.query(TrackedShop).filter(
        TrackedShop.user_id == current_user.id,
        TrackedShop.shop_id == shop_id
    ).first()
    
    if not tracked_shop:
        raise HTTPException(status_code=404, detail="Tracked shop not found")
    
    db.delete(tracked_shop)
    db.commit()
    
    return {"message": "Shop removed from favorites"}

