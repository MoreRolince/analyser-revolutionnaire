#!/usr/bin/env python3
"""
Script pour vérifier un utilisateur et tester la connexion
Usage:
    python check_user.py <email>  # Vérifier un utilisateur par email
    python check_user.py --all     # Lister tous les utilisateurs
"""

import sys

try:
    from sqlalchemy.orm import Session
    from app.database import SessionLocal
    from app.models import User, UserRole, UserStatus
    from app.auth import verify_password, get_password_hash
except ImportError as e:
    print(f"❌ Erreur d'import: {e}")
    print("\n💡 Assurez-vous d'être dans l'environnement virtuel:")
    print("   source env/bin/activate  # Linux/Mac")
    sys.exit(1)

def check_user(email: str, db: Session):
    """Vérifie un utilisateur et teste le mot de passe"""
    user = db.query(User).filter(User.email == email).first()
    
    if not user:
        print(f"❌ Aucun utilisateur trouvé avec l'email: {email}")
        return False
    
    print(f"\n📋 Informations de l'utilisateur:")
    print("-" * 60)
    print(f"  ID: {user.id}")
    print(f"  Email: {user.email}")
    print(f"  Nom: {user.name}")
    print(f"  Rôle: {user.role}")
    print(f"  Statut: {user.status}")
    print(f"  Actif: {user.is_active}")
    print(f"  Plan: {user.plan}")
    print(f"  Créé le: {user.created_at}")
    print("-" * 60)
    
    # Vérifier le statut
    if user.status != UserStatus.APPROVED.value:
        print(f"\n⚠️  ATTENTION: Le compte n'est pas approuvé!")
        print(f"   Statut actuel: {user.status}")
        print(f"   Statut requis: {UserStatus.APPROVED.value}")
        print(f"\n   Pour approuver ce compte, utilisez:")
        print(f"   curl -X POST 'http://localhost:8000/api/v1/admin/users/{user.id}/approve?approve=true' \\")
        print(f"     -H 'Authorization: Bearer <token_admin>'")
        return False
    
    # Tester le mot de passe
    print(f"\n🔐 Test de mot de passe:")
    password = input("  Entrez le mot de passe à tester: ")
    
    if verify_password(password, user.hashed_password):
        print("  ✅ Mot de passe correct!")
        print(f"\n✅ Le compte est prêt à être utilisé!")
        print(f"\n   Pour vous connecter:")
        print(f"   curl -X POST 'http://localhost:8000/api/v1/auth/login' \\")
        print(f"     -H 'Content-Type: application/x-www-form-urlencoded' \\")
        print(f"     -d 'username={user.email}&password={password}'")
    else:
        print("  ❌ Mot de passe incorrect!")
        print(f"\n   Le hash stocké est: {user.hashed_password[:50]}...")
        return False
    
    return True

def list_all_users(db: Session):
    """Liste tous les utilisateurs"""
    users = db.query(User).order_by(User.created_at.desc()).all()
    
    if not users:
        print("ℹ️  Aucun utilisateur trouvé dans la base de données.")
        return
    
    print(f"\n📋 Liste de tous les utilisateurs ({len(users)}):")
    print("-" * 100)
    print(f"{'ID':<5} | {'Email':<30} | {'Nom':<20} | {'Rôle':<10} | {'Statut':<12} | {'Actif':<6}")
    print("-" * 100)
    
    for user in users:
        role_str = str(user.role).split('.')[-1] if user.role else "N/A"
        status_str = user.status or "N/A"
        active_str = "Oui" if user.is_active else "Non"
        
        print(f"{user.id:<5} | {user.email:<30} | {user.name[:20]:<20} | {role_str:<10} | {status_str:<12} | {active_str:<6}")
    
    print("-" * 100)
    
    # Statistiques
    approved = sum(1 for u in users if u.status == UserStatus.APPROVED.value)
    pending = sum(1 for u in users if u.status == UserStatus.PENDING.value)
    rejected = sum(1 for u in users if u.status == UserStatus.REJECTED.value)
    admins = sum(1 for u in users if u.role == UserRole.ADMIN)
    
    print(f"\n📊 Statistiques:")
    print(f"  Total: {len(users)}")
    print(f"  Approuvés: {approved}")
    print(f"  En attente: {pending}")
    print(f"  Rejetés: {rejected}")
    print(f"  Admins: {admins}")

def main():
    db = SessionLocal()
    try:
        if len(sys.argv) < 2:
            print("Usage:")
            print("  python check_user.py <email>  # Vérifier un utilisateur")
            print("  python check_user.py --all    # Lister tous les utilisateurs")
            sys.exit(1)
        
        arg = sys.argv[1]
        
        if arg == "--all":
            list_all_users(db)
        else:
            email = arg.strip()
            check_user(email, db)
    
    except KeyboardInterrupt:
        print("\n\n❌ Opération annulée.")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Erreur: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    finally:
        db.close()

if __name__ == "__main__":
    main()
