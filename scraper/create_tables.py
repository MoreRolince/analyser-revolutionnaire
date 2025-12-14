"""
Script pour créer les tables Facebook Ads dans la base de données
"""
import os
import sys

# Ajouter les chemins pour les imports
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)
backend_path = os.path.join(project_root, 'backend')

if backend_path not in sys.path:
    sys.path.insert(0, backend_path)

from sqlalchemy import create_engine
from app.database import Base
from app.models import FacebookAdRaw, DigitalProductDetected, DigitalProductScore

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://marketpulse:marketpulse_password@localhost:5433/marketpulse"
)

print("🔧 Création des tables Facebook Ads...")
print(f"Base de données: {DATABASE_URL.split('@')[1] if '@' in DATABASE_URL else DATABASE_URL}")

try:
    engine = create_engine(DATABASE_URL)
    Base.metadata.create_all(bind=engine)
    print("✅ Tables créées avec succès!")
    print("   - fb_ads_raw")
    print("   - digital_products_detected")
    print("   - digital_products_scores")
except Exception as e:
    print(f"❌ Erreur lors de la création des tables: {e}")
    import traceback
    traceback.print_exc()


Script pour créer les tables Facebook Ads dans la base de données
"""
import os
import sys

# Ajouter les chemins pour les imports
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)
backend_path = os.path.join(project_root, 'backend')

if backend_path not in sys.path:
    sys.path.insert(0, backend_path)

from sqlalchemy import create_engine
from app.database import Base
from app.models import FacebookAdRaw, DigitalProductDetected, DigitalProductScore

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://marketpulse:marketpulse_password@localhost:5433/marketpulse"
)

print("🔧 Création des tables Facebook Ads...")
print(f"Base de données: {DATABASE_URL.split('@')[1] if '@' in DATABASE_URL else DATABASE_URL}")

try:
    engine = create_engine(DATABASE_URL)
    Base.metadata.create_all(bind=engine)
    print("✅ Tables créées avec succès!")
    print("   - fb_ads_raw")
    print("   - digital_products_detected")
    print("   - digital_products_scores")
except Exception as e:
    print(f"❌ Erreur lors de la création des tables: {e}")
    import traceback
    traceback.print_exc()

