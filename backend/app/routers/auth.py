from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from datetime import timedelta
import os
import shutil
import time
from pathlib import Path

from app.database import get_db
from app.models import User, UserStatus
from app.schemas import UserRegister, Token, UserResponse
from app.auth import (
    verify_password,
    get_password_hash,
    create_access_token,
    get_current_active_user,
    ACCESS_TOKEN_EXPIRE_MINUTES
)

router = APIRouter()

def calculate_quota(user: User) -> dict:
    """Calcule les quotas selon le plan de l'utilisateur"""
    if user.plan == "3months":
        return {
            "analyses": 100,
            "aiRequests": 500,
            "trackedShops": 10
        }
    elif user.plan == "6months":
        return {
            "analyses": 300,
            "aiRequests": 1500,
            "trackedShops": 30
        }
    else:  # trial
        return {
            "analyses": 10,
            "aiRequests": 50,
            "trackedShops": 3
        }

# Créer le dossier pour les uploads si il n'existe pas
UPLOAD_DIR = Path("uploads/payment_proofs")
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

@router.post("/register")
async def register(
    name: str = Form(...),
    email: str = Form(...),
    password: str = Form(...),
    plan: str = Form("trial"),
    payment_proof: UploadFile = File(None),
    db: Session = Depends(get_db)
):
    # Vérifier si l'email existe déjà
    existing_user = db.query(User).filter(User.email == email).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    # Valider le plan
    valid_plans = ["trial", "3months", "6months"]
    if plan not in valid_plans:
        plan = "trial"
    
    # Vérifier que si le plan n'est pas trial, une preuve de paiement est fournie
    if plan != "trial" and not payment_proof:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Une preuve de paiement est requise pour les plans payants"
        )
    
    # Créer l'utilisateur en attente de validation
    hashed_password = get_password_hash(password)
    db_user = User(
        email=email,
        name=name,
        hashed_password=hashed_password,
        status=UserStatus.PENDING.value,  # En attente de validation par l'admin
        plan=plan
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    
    # Gérer la preuve de paiement si fournie
    proof_url = None
    if payment_proof:
        try:
            # Générer un nom de fichier unique
            file_extension = Path(payment_proof.filename).suffix
            unique_filename = f"{db_user.id}_{db_user.email.replace('@', '_at_')}_{int(time.time())}{file_extension}"
            file_path = UPLOAD_DIR / unique_filename
            
            # Sauvegarder le fichier
            with open(file_path, "wb") as buffer:
                shutil.copyfileobj(payment_proof.file, buffer)
            
            # Créer l'URL relative
            proof_url = f"/uploads/payment_proofs/{unique_filename}"
            
            # Créer un enregistrement de paiement
            from app.models import Payment, PaymentStatus
            
            # Déterminer le montant selon le plan
            amount = 15000.0 if plan == "3months" else 25000.0
            
            db_payment = Payment(
                user_id=db_user.id,
                plan=plan,
                amount=amount,
                proof_url=proof_url,
                status=PaymentStatus.PENDING.value
            )
            db.add(db_payment)
            db.commit()
            
        except Exception as e:
            # Si l'upload échoue, on continue quand même l'inscription
            print(f"Erreur lors de l'upload de la preuve de paiement: {e}")
    
    # Retourner une réponse indiquant que l'inscription est en attente
    return {
        "id": db_user.id,
        "email": db_user.email,
        "name": db_user.name,
        "status": db_user.status,
        "message": "Votre inscription est en attente de validation. Vous recevrez un email une fois votre compte activé."
    }

@router.post("/login", response_model=Token)
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
):
    user = db.query(User).filter(User.email == form_data.username).first()
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Vérifier que l'utilisateur est approuvé
    if user.status != UserStatus.APPROVED.value:
        if user.status == UserStatus.PENDING.value:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Votre compte est en attente de validation. Veuillez patienter, vous recevrez un email une fois votre compte activé."
            )
        elif user.status == UserStatus.REJECTED.value:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Votre compte a été rejeté. Veuillez contacter le support."
            )
    
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": str(user.id)}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}

@router.get("/me", response_model=UserResponse)
async def read_users_me(current_user: User = Depends(get_current_active_user)):
    return UserResponse(
        id=current_user.id,
        email=current_user.email,
        name=current_user.name,
        role=current_user.role,
        plan=current_user.plan,
        quota=calculate_quota(current_user)
    )


            
            # Créer l'URL relative
            proof_url = f"/uploads/payment_proofs/{unique_filename}"
            
            # Créer un enregistrement de paiement
            from app.models import Payment, PaymentStatus
            
            # Déterminer le montant selon le plan
            amount = 15000.0 if plan == "3months" else 25000.0
            
            db_payment = Payment(
                user_id=db_user.id,
                plan=plan,
                amount=amount,
                proof_url=proof_url,
                status=PaymentStatus.PENDING.value
            )
            db.add(db_payment)
            db.commit()
            
        except Exception as e:
            # Si l'upload échoue, on continue quand même l'inscription
            print(f"Erreur lors de l'upload de la preuve de paiement: {e}")
    
    # Retourner une réponse indiquant que l'inscription est en attente
    return {
        "id": db_user.id,
        "email": db_user.email,
        "name": db_user.name,
        "status": db_user.status,
        "message": "Votre inscription est en attente de validation. Vous recevrez un email une fois votre compte activé."
    }

@router.post("/login", response_model=Token)
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
):
    user = db.query(User).filter(User.email == form_data.username).first()
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Vérifier que l'utilisateur est approuvé
    if user.status != UserStatus.APPROVED.value:
        if user.status == UserStatus.PENDING.value:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Votre compte est en attente de validation. Veuillez patienter, vous recevrez un email une fois votre compte activé."
            )
        elif user.status == UserStatus.REJECTED.value:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Votre compte a été rejeté. Veuillez contacter le support."
            )
    
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": str(user.id)}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}

@router.get("/me", response_model=UserResponse)
async def read_users_me(current_user: User = Depends(get_current_active_user)):
    return UserResponse(
        id=current_user.id,
        email=current_user.email,
        name=current_user.name,
        role=current_user.role,
        plan=current_user.plan,
        quota=calculate_quota(current_user)
    )

