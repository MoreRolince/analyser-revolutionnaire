#!/usr/bin/env python3
"""
Script pour créer ou promouvoir un utilisateur admin
Usage:
    python create_admin.py --create          # Créer un nouvel admin (avec confirmation de mot de passe)
    python create_admin.py --create-direct   # Créer un admin (champs demandés un par un, sans confirmation)
    python create_admin.py --promote <email> # Promouvoir un utilisateur existant
    python create_admin.py --list            # Lister tous les admins

Exemples:
    # Création directe (recommandé pour les tests)
    python create_admin.py --create-direct
    # Le script demandera: Email, Nom, Mot de passe (un par un)
    
    # Mode interactif avec confirmation
    python create_admin.py --create

Note: Assurez-vous d'être dans l'environnement virtuel avant d'exécuter ce script:
    source env/bin/activate  # Linux/Mac
"""

import sys
import getpass

# Vérifier les imports critiques
try:
    from sqlalchemy.orm import Session
    from app.database import SessionLocal
    from app.models import User, UserRole, UserStatus
    from app.auth import get_password_hash
except ImportError as e:
    print(f"❌ Erreur d'import: {e}")
    print("\n💡 Assurez-vous d'être dans l'environnement virtuel:")
    print("   source env/bin/activate  # Linux/Mac")
    print("   env\\Scripts\\activate     # Windows")
    sys.exit(1)

def create_admin_user(email: str, name: str, password: str, db: Session):
    """Crée un nouvel utilisateur admin"""
    # Vérifier si l'email existe déjà
    existing_user = db.query(User).filter(User.email == email).first()
    if existing_user:
        print(f"❌ Erreur: Un utilisateur avec l'email '{email}' existe déjà.")
        print(f"   Utilisez --promote {email} pour le promouvoir en admin.")
        return False
    
    # Créer le nouvel utilisateur admin
    hashed_password = get_password_hash(password)
    admin_user = User(
        email=email,
        name=name,
        hashed_password=hashed_password,
        role=UserRole.ADMIN,
        status=UserStatus.APPROVED.value,  # Admin approuvé automatiquement
        is_active=True
    )
    
    db.add(admin_user)
    db.commit()
    db.refresh(admin_user)
    
    print(f"✅ Admin créé avec succès!")
    print(f"   ID: {admin_user.id}")
    print(f"   Email: {admin_user.email}")
    print(f"   Nom: {admin_user.name}")
    print(f"   Rôle: {admin_user.role}")
    print(f"   Statut: {admin_user.status}")
    return True

def promote_to_admin(email: str, db: Session):
    """Promouvoit un utilisateur existant en admin"""
    user = db.query(User).filter(User.email == email).first()
    if not user:
        print(f"❌ Erreur: Aucun utilisateur trouvé avec l'email '{email}'")
        return False
    
    if user.role == UserRole.ADMIN:
        print(f"ℹ️  L'utilisateur '{email}' est déjà admin.")
        return False
    
    # Promouvoir en admin
    user.role = UserRole.ADMIN
    # S'assurer que l'admin est approuvé
    if user.status != UserStatus.APPROVED.value:
        user.status = UserStatus.APPROVED.value
        print(f"   → Statut également mis à jour à 'approved'")
    
    db.commit()
    
    print(f"✅ Utilisateur promu en admin avec succès!")
    print(f"   ID: {user.id}")
    print(f"   Email: {user.email}")
    print(f"   Nom: {user.name}")
    print(f"   Rôle: {user.role} (mis à jour)")
    print(f"   Statut: {user.status}")
    return True

def list_admins(db: Session):
    """Liste tous les admins"""
    admins = db.query(User).filter(User.role == UserRole.ADMIN).all()
    if not admins:
        print("ℹ️  Aucun admin trouvé dans la base de données.")
        return
    
    print(f"\n📋 Liste des admins ({len(admins)}):")
    print("-" * 80)
    for admin in admins:
        print(f"  ID: {admin.id:4d} | Email: {admin.email:30s} | Nom: {admin.name:20s} | Statut: {admin.status}")
    print("-" * 80)

def main():
    db = SessionLocal()
    try:
        if len(sys.argv) < 2:
            print("Usage:")
            print("  python create_admin.py --create          # Créer un nouvel admin (avec confirmation)")
            print("  python create_admin.py --create-direct   # Créer un admin (champs demandés un par un)")
            print("  python create_admin.py --promote <email>  # Promouvoir un utilisateur existant")
            print("  python create_admin.py --list             # Lister tous les admins")
            print("\nNote: --create-direct demande les champs un par un (sans confirmation de mot de passe)")
            sys.exit(1)
        
        command = sys.argv[1]
        
        if command == "--create":
            print("\n🔐 Création d'un nouvel utilisateur admin (mode interactif)")
            print("-" * 50)
            
            email = input("Email: ").strip()
            if not email:
                print("❌ L'email est requis.")
                sys.exit(1)
            
            name = input("Nom: ").strip()
            if not name:
                print("❌ Le nom est requis.")
                sys.exit(1)
            
            password = getpass.getpass("Mot de passe: ")
            if len(password) < 8:
                print("❌ Le mot de passe doit contenir au moins 8 caractères.")
                sys.exit(1)
            
            password_confirm = getpass.getpass("Confirmer le mot de passe: ")
            if password != password_confirm:
                print("❌ Les mots de passe ne correspondent pas.")
                sys.exit(1)
            
            print()
            create_admin_user(email, name, password, db)
        
        elif command == "--create-direct":
            print("\n🔐 Création d'un nouvel utilisateur admin")
            print("-" * 50)
            
            # Demander l'email
            if len(sys.argv) >= 3:
                email = sys.argv[2].strip()
            else:
                email = input("Email: ").strip()
            
            if not email or "@" not in email:
                print("❌ Email invalide.")
                sys.exit(1)
            
            # Demander le nom
            if len(sys.argv) >= 4:
                name = sys.argv[3].strip()
            else:
                name = input("Nom: ").strip()
            
            if not name:
                print("❌ Le nom est requis.")
                sys.exit(1)
            
            # Demander le mot de passe
            if len(sys.argv) >= 5:
                password = sys.argv[4].strip()
            else:
                password = getpass.getpass("Mot de passe: ")
            
            if len(password) < 8:
                print("❌ Le mot de passe doit contenir au moins 8 caractères.")
                sys.exit(1)
            
            print()
            create_admin_user(email, name, password, db)
        
        elif command == "--promote":
            if len(sys.argv) < 3:
                print("❌ Usage: python create_admin.py --promote <email>")
                sys.exit(1)
            
            email = sys.argv[2].strip()
            print(f"\n⬆️  Promotion de l'utilisateur '{email}' en admin")
            print("-" * 50)
            promote_to_admin(email, db)
        
        elif command == "--list":
            list_admins(db)
        
        else:
            print(f"❌ Commande inconnue: {command}")
            print("Utilisez --create, --create-direct, --promote ou --list")
            sys.exit(1)
    
    except KeyboardInterrupt:
        print("\n\n❌ Opération annulée par l'utilisateur.")
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
