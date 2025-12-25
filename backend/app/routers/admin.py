from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List, Optional, Dict

from app.database import get_db
from app.models import User, Payment, PaymentStatus, AdminLog, UserStatus, PlanType
from app.schemas import PaymentApproval, UserResponse
from app.auth import get_current_admin_user
from typing import List

router = APIRouter()

@router.get("/users", response_model=List[UserResponse])
async def list_users(
    skip: int = 0,
    limit: int = 100,
    status: Optional[str] = None,
    admin_user: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    query = db.query(User)
    if status:
        try:
            status_value = status.lower()
            query = query.filter(User.status == status_value)
        except ValueError:
            pass
    users = query.order_by(User.created_at.desc()).offset(skip).limit(limit).all()
    # Convertir les utilisateurs en format de réponse avec created_at
    result = []
    for user in users:
        user_dict = {
            "id": user.id,
            "email": user.email,
            "name": user.name,
            "role": user.role,
            "status": user.status,
            "plan": user.plan,
            "quota": {},
            "created_at": user.created_at.isoformat() if user.created_at else None
        }
        result.append(user_dict)
    return result

@router.get("/users/pending", response_model=List[UserResponse])
async def get_pending_users(
    admin_user: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """Récupère la liste des utilisateurs en attente de validation"""
    users = db.query(User).filter(User.status == UserStatus.PENDING.value).order_by(User.created_at.desc()).all()
    # Convertir les utilisateurs en format de réponse avec created_at
    result = []
    for user in users:
        user_dict = {
            "id": user.id,
            "email": user.email,
            "name": user.name,
            "role": user.role,
            "status": user.status,
            "plan": user.plan,
            "quota": {},
            "created_at": user.created_at.isoformat() if user.created_at else None
        }
        result.append(user_dict)
    return result

@router.post("/users/{user_id}/approve")
async def approve_user(
    user_id: int,
    approve: bool = True,
    admin_user: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """Approuve ou rejette un utilisateur"""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    if approve:
        user.status = UserStatus.APPROVED.value
        message = "Utilisateur approuvé avec succès"
    else:
        user.status = UserStatus.REJECTED.value
        message = "Utilisateur rejeté"
    
    # Logger l'action
    log = AdminLog(
        admin_id=admin_user.id,
        action="user_approval",
        target_type="user",
        target_id=user_id,
        details={"approved": approve, "user_email": user.email}
    )
    db.add(log)
    db.commit()
    
    return {"message": message, "user": UserResponse(
        id=user.id,
        email=user.email,
        name=user.name,
        role=user.role,
        status=user.status,
        plan=user.plan,
        quota={}
    )}

@router.get("/payments/pending")
async def get_pending_payments(
    admin_user: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    payments = db.query(Payment).filter(
        Payment.status == PaymentStatus.PENDING
    ).all()
    # Inclure l'email de l'utilisateur dans la réponse
    result = []
    for payment in payments:
        user = db.query(User).filter(User.id == payment.user_id).first()
        payment_dict = {
            "id": payment.id,
            "user_id": payment.user_id,
            "user_email": user.email if user else "N/A",
            "plan": payment.plan,
            "amount": payment.amount,
            "proof_url": payment.proof_url,
            "status": payment.status,
            "created_at": payment.created_at.isoformat() if payment.created_at else None
        }
        result.append(payment_dict)
    return result

@router.post("/payments/{payment_id}/approve")
async def approve_payment(
    payment_id: int,
    approval: PaymentApproval,
    admin_user: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    payment = db.query(Payment).filter(Payment.id == payment_id).first()
    if not payment:
        raise HTTPException(status_code=404, detail="Payment not found")
    
    if approval.approve:
        payment.status = PaymentStatus.APPROVED
        payment.approved_by = admin_user.id

        # Mettre à jour le plan de l'utilisateur
        user = db.query(User).filter(User.id == payment.user_id).first()
        if user:
            # S'assurer que le plan est bien un PlanType
            user.plan = payment.plan if isinstance(payment.plan, PlanType) else PlanType(payment.plan)
            # Calculer les dates de fin de plan
            from datetime import datetime, timedelta
            user.plan_start_date = datetime.utcnow()
            if user.plan == PlanType.THREE_MONTHS:
                user.plan_end_date = datetime.utcnow() + timedelta(days=90)
            elif user.plan == PlanType.SIX_MONTHS:
                user.plan_end_date = datetime.utcnow() + timedelta(days=180)
    else:
        payment.status = PaymentStatus.REJECTED
        payment.approved_by = admin_user.id
    
    # Logger l'action
    log = AdminLog(
        admin_id=admin_user.id,
        action="payment_approval",
        target_type="payment",
        target_id=payment_id,
        details={"approved": approval.approve}
    )
    db.add(log)
    db.commit()
    
    return {"message": "Payment updated successfully"}

@router.get("/logs")
async def get_admin_logs(
    skip: int = 0,
    limit: int = 100,
    admin_user: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    logs = db.query(AdminLog).order_by(AdminLog.created_at.desc()).offset(skip).limit(limit).all()
    return logs

@router.get("/stats")
async def get_admin_stats(
    admin_user: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """Récupère les statistiques globales pour le dashboard admin"""
    # Total utilisateurs
    total_users = db.query(User).count()
    
    # Utilisateurs par statut
    users_by_status = db.query(
        User.status,
        func.count(User.id).label('count')
    ).group_by(User.status).all()
    
    status_counts = {status: count for status, count in users_by_status}
    
    # Utilisateurs par plan
    users_by_plan = db.query(
        User.plan,
        func.count(User.id).label('count')
    ).filter(User.status == UserStatus.APPROVED.value).group_by(User.plan).all()
    
    plan_counts = {plan or 'trial': count for plan, count in users_by_plan}
    
    # Utilisateurs actifs (approuvés)
    active_users = db.query(User).filter(User.status == UserStatus.APPROVED.value).count()
    
    # Paiements en attente
    pending_payments = db.query(Payment).filter(Payment.status == PaymentStatus.PENDING).count()
    
    # Utilisateurs en attente
    pending_users = db.query(User).filter(User.status == UserStatus.PENDING.value).count()
    
    return {
        "total_users": total_users,
        "active_users": active_users,
        "pending_users": pending_users,
        "users_by_status": status_counts,
        "users_by_plan": plan_counts,
        "pending_payments": pending_payments
    }

