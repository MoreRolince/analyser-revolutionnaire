"""
Script pour créer des utilisateurs de test
"""
import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from app.database import SessionLocal
from app.auth import get_password_hash
from sqlalchemy import text

def create_test_users():
    db = SessionLocal()
    
    try:
        # Créer un utilisateur test normal avec SQL direct
        result = db.execute(text("SELECT id FROM users WHERE email = :email"), {"email": "test@marketpulse.africa"})
        test_user_exists = result.first()
        
        if not test_user_exists:
            hashed_password = get_password_hash("test123456")
            db.execute(text("""
                INSERT INTO users (email, name, hashed_password, role, status, plan, is_active)
                VALUES (:email, :name, :password, 'USER'::userrole, 'approved'::userstatus, 'TRIAL'::plantype, true)
            """), {
                "email": "test@marketpulse.africa",
                "name": "Utilisateur Test",
                "password": hashed_password
            })
            print("✅ Utilisateur test créé: test@marketpulse.africa / test123456")
        else:
            print("ℹ️  Utilisateur test existe déjà")
        
        # Créer un admin test
        result = db.execute(text("SELECT id FROM users WHERE email = :email"), {"email": "admin@marketpulse.africa"})
        admin_user_exists = result.first()
        
        if not admin_user_exists:
            hashed_password = get_password_hash("admin123456")
            db.execute(text("""
                INSERT INTO users (email, name, hashed_password, role, status, plan, is_active)
                VALUES (:email, :name, :password, 'ADMIN'::userrole, 'approved'::userstatus, 'SIX_MONTHS'::plantype, true)
            """), {
                "email": "admin@marketpulse.africa",
                "name": "Admin Test",
                "password": hashed_password
            })
            print("✅ Admin test créé: admin@marketpulse.africa / admin123456")
        else:
            print("ℹ️  Admin test existe déjà")
        
        db.commit()
        print("\n✅ Utilisateurs de test créés avec succès!")
        print("\n📋 Comptes créés:")
        print("   👤 Utilisateur: test@marketpulse.africa / test123456")
        print("   👨‍💼 Admin: admin@marketpulse.africa / admin123456")
        
    except Exception as e:
        db.rollback()
        print(f"❌ Erreur: {e}")
        import traceback
        traceback.print_exc()
        raise
    finally:
        db.close()

if __name__ == "__main__":
    create_test_users()

"""
import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from app.database import SessionLocal
from app.auth import get_password_hash
from sqlalchemy import text

def create_test_users():
    db = SessionLocal()
    
    try:
        # Créer un utilisateur test normal avec SQL direct
        result = db.execute(text("SELECT id FROM users WHERE email = :email"), {"email": "test@marketpulse.africa"})
        test_user_exists = result.first()
        
        if not test_user_exists:
            hashed_password = get_password_hash("test123456")
            db.execute(text("""
                INSERT INTO users (email, name, hashed_password, role, status, plan, is_active)
                VALUES (:email, :name, :password, 'USER'::userrole, 'approved'::userstatus, 'TRIAL'::plantype, true)
            """), {
                "email": "test@marketpulse.africa",
                "name": "Utilisateur Test",
                "password": hashed_password
            })
            print("✅ Utilisateur test créé: test@marketpulse.africa / test123456")
        else:
            print("ℹ️  Utilisateur test existe déjà")
        
        # Créer un admin test
        result = db.execute(text("SELECT id FROM users WHERE email = :email"), {"email": "admin@marketpulse.africa"})
        admin_user_exists = result.first()
        
        if not admin_user_exists:
            hashed_password = get_password_hash("admin123456")
            db.execute(text("""
                INSERT INTO users (email, name, hashed_password, role, status, plan, is_active)
                VALUES (:email, :name, :password, 'ADMIN'::userrole, 'approved'::userstatus, 'SIX_MONTHS'::plantype, true)
            """), {
                "email": "admin@marketpulse.africa",
                "name": "Admin Test",
                "password": hashed_password
            })
            print("✅ Admin test créé: admin@marketpulse.africa / admin123456")
        else:
            print("ℹ️  Admin test existe déjà")
        
        db.commit()
        print("\n✅ Utilisateurs de test créés avec succès!")
        print("\n📋 Comptes créés:")
        print("   👤 Utilisateur: test@marketpulse.africa / test123456")
        print("   👨‍💼 Admin: admin@marketpulse.africa / admin123456")
        
    except Exception as e:
        db.rollback()
        print(f"❌ Erreur: {e}")
        import traceback
        traceback.print_exc()
        raise
    finally:
        db.close()

if __name__ == "__main__":
    create_test_users()
