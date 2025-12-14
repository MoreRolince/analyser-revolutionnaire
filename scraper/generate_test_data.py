"""
Génère des données de test réalistes pour avoir plus de statistiques
"""
import os
import sys
from datetime import datetime, timedelta
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import random

# Ajouter les chemins
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
backend_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'backend')
sys.path.insert(0, backend_path)

from services.continuous_scraper import import_backend_models

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://marketpulse:marketpulse_password@localhost:5433/marketpulse"
)

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(bind=engine)

# Données de test réalistes
SHOP_NAMES = [
    "TechZone Africa", "Digital Market", "AfroShop", "E-Commerce Hub",
    "Business Store", "Online Market", "Shop Africa", "Digital Store",
    "Tech Market", "Business Hub", "Online Shop", "Market Place",
    "Digital Hub", "Tech Store", "Business Market", "Shop Online",
    "Market Hub", "Digital Shop", "Tech Hub", "Business Online"
]

PRODUCT_NAMES = [
    "Formation en ligne", "Cours vidéo", "E-book", "Template",
    "Service digital", "Consultation", "Coaching", "Mentorat",
    "Produit numérique", "Ressource", "Guide pratique", "Formation",
    "Programme", "Accompagnement", "Support", "Outils",
    "Kit complet", "Pack premium", "Formation avancée", "Masterclass"
]

CATEGORIES = [
    "Formation", "Business", "Marketing", "Développement",
    "Design", "Finance", "Santé", "Bien-être"
]

def generate_test_data():
    """Génère des données de test"""
    print("="*70)
    print("🚀 GÉNÉRATION DE DONNÉES DE TEST")
    print("="*70)
    print()
    
    db = SessionLocal()
    
    try:
        ShopGlobal, ProductGlobal, MarketplaceType = import_backend_models()
        
        # Générer 20 boutiques
        print("📦 Génération de boutiques...")
        shops_created = 0
        
        for i in range(20):
            marketplace = random.choice(["chariow", "maketou"])
            shop_name = random.choice(SHOP_NAMES) + f" {i+1}"
            shop_url = f"https://{shop_name.lower().replace(' ', '')}.my{marketplace}.{'shop' if marketplace == 'chariow' else 'store'}/"
            
            # Vérifier si la boutique existe déjà
            existing = db.query(ShopGlobal).filter(
                ShopGlobal.shop_url == shop_url
            ).first()
            
            if not existing:
                shop = ShopGlobal(
                    marketplace=marketplace,
                    shop_name=shop_name,
                    shop_url=shop_url,
                    score_global=random.uniform(30, 90),
                    revenue_est_min=random.uniform(100000, 5000000),
                    revenue_est_max=random.uniform(500000, 10000000),
                    winners_count=random.randint(0, 15),
                    last_scraped_at=datetime.utcnow() - timedelta(hours=random.randint(0, 48))
                )
                db.add(shop)
                shops_created += 1
        
        db.commit()
        print(f"✅ {shops_created} nouvelles boutiques créées")
        print()
        
        # Générer des produits pour chaque boutique
        print("📦 Génération de produits...")
        all_shops = db.query(ShopGlobal).all()
        products_created = 0
        
        for shop in all_shops:
            # Générer 5-20 produits par boutique
            num_products = random.randint(5, 20)
            
            for i in range(num_products):
                product_name = random.choice(PRODUCT_NAMES) + f" {i+1}"
                product_url = f"{shop.shop_url}product/{product_name.lower().replace(' ', '-')}"
                
                # Vérifier si le produit existe déjà
                existing = db.query(ProductGlobal).filter(
                    ProductGlobal.product_url == product_url
                ).first()
                
                if not existing:
                    price = random.uniform(5000, 50000)
                    score = random.uniform(40, 95)
                    sales_min = random.randint(10, 50)
                    sales_max = sales_min + random.randint(10, 30)
                    
                    product = ProductGlobal(
                        marketplace=shop.marketplace,
                        product_name=product_name,
                        shop_name=shop.shop_name,
                        product_url=product_url,
                        price=price,
                        sales_est_min=sales_min,
                        sales_est_max=sales_max,
                        revenue_est_min=price * sales_min * 0.7,
                        revenue_est_max=price * sales_max,
                        score_winner=score,
                        category=random.choice(CATEGORIES),
                        last_scraped_at=datetime.utcnow() - timedelta(hours=random.randint(0, 72))
                    )
                    db.add(product)
                    products_created += 1
        
        db.commit()
        print(f"✅ {products_created} nouveaux produits créés")
        print()
        
        # Statistiques finales
        total_shops = db.query(ShopGlobal).count()
        total_products = db.query(ProductGlobal).count()
        total_winners = db.query(ProductGlobal).filter(ProductGlobal.score_winner >= 70).count()
        from sqlalchemy import func
        avg_score = db.query(func.avg(ProductGlobal.score_winner)).scalar() or 0
        
        print("="*70)
        print("📊 STATISTIQUES FINALES")
        print("="*70)
        print(f"🏪 Total boutiques: {total_shops}")
        print(f"📦 Total produits: {total_products}")
        print(f"⭐ Produits winners (score >= 70): {total_winners}")
        print(f"📈 Score moyen: {avg_score:.1f}/100")
        print()
        
        # Par marketplace
        for marketplace in ["chariow", "maketou"]:
            shops_count = db.query(ShopGlobal).filter(ShopGlobal.marketplace == marketplace).count()
            products_count = db.query(ProductGlobal).filter(ProductGlobal.marketplace == marketplace).count()
            print(f"   {marketplace.upper()}: {shops_count} boutiques, {products_count} produits")
        
        print()
        print("✅ Génération terminée!")
        
    finally:
        db.close()

if __name__ == "__main__":
    generate_test_data()


"""
import os
import sys
from datetime import datetime, timedelta
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import random

# Ajouter les chemins
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
backend_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'backend')
sys.path.insert(0, backend_path)

from services.continuous_scraper import import_backend_models

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://marketpulse:marketpulse_password@localhost:5433/marketpulse"
)

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(bind=engine)

# Données de test réalistes
SHOP_NAMES = [
    "TechZone Africa", "Digital Market", "AfroShop", "E-Commerce Hub",
    "Business Store", "Online Market", "Shop Africa", "Digital Store",
    "Tech Market", "Business Hub", "Online Shop", "Market Place",
    "Digital Hub", "Tech Store", "Business Market", "Shop Online",
    "Market Hub", "Digital Shop", "Tech Hub", "Business Online"
]

PRODUCT_NAMES = [
    "Formation en ligne", "Cours vidéo", "E-book", "Template",
    "Service digital", "Consultation", "Coaching", "Mentorat",
    "Produit numérique", "Ressource", "Guide pratique", "Formation",
    "Programme", "Accompagnement", "Support", "Outils",
    "Kit complet", "Pack premium", "Formation avancée", "Masterclass"
]

CATEGORIES = [
    "Formation", "Business", "Marketing", "Développement",
    "Design", "Finance", "Santé", "Bien-être"
]

def generate_test_data():
    """Génère des données de test"""
    print("="*70)
    print("🚀 GÉNÉRATION DE DONNÉES DE TEST")
    print("="*70)
    print()
    
    db = SessionLocal()
    
    try:
        ShopGlobal, ProductGlobal, MarketplaceType = import_backend_models()
        
        # Générer 20 boutiques
        print("📦 Génération de boutiques...")
        shops_created = 0
        
        for i in range(20):
            marketplace = random.choice(["chariow", "maketou"])
            shop_name = random.choice(SHOP_NAMES) + f" {i+1}"
            shop_url = f"https://{shop_name.lower().replace(' ', '')}.my{marketplace}.{'shop' if marketplace == 'chariow' else 'store'}/"
            
            # Vérifier si la boutique existe déjà
            existing = db.query(ShopGlobal).filter(
                ShopGlobal.shop_url == shop_url
            ).first()
            
            if not existing:
                shop = ShopGlobal(
                    marketplace=marketplace,
                    shop_name=shop_name,
                    shop_url=shop_url,
                    score_global=random.uniform(30, 90),
                    revenue_est_min=random.uniform(100000, 5000000),
                    revenue_est_max=random.uniform(500000, 10000000),
                    winners_count=random.randint(0, 15),
                    last_scraped_at=datetime.utcnow() - timedelta(hours=random.randint(0, 48))
                )
                db.add(shop)
                shops_created += 1
        
        db.commit()
        print(f"✅ {shops_created} nouvelles boutiques créées")
        print()
        
        # Générer des produits pour chaque boutique
        print("📦 Génération de produits...")
        all_shops = db.query(ShopGlobal).all()
        products_created = 0
        
        for shop in all_shops:
            # Générer 5-20 produits par boutique
            num_products = random.randint(5, 20)
            
            for i in range(num_products):
                product_name = random.choice(PRODUCT_NAMES) + f" {i+1}"
                product_url = f"{shop.shop_url}product/{product_name.lower().replace(' ', '-')}"
                
                # Vérifier si le produit existe déjà
                existing = db.query(ProductGlobal).filter(
                    ProductGlobal.product_url == product_url
                ).first()
                
                if not existing:
                    price = random.uniform(5000, 50000)
                    score = random.uniform(40, 95)
                    sales_min = random.randint(10, 50)
                    sales_max = sales_min + random.randint(10, 30)
                    
                    product = ProductGlobal(
                        marketplace=shop.marketplace,
                        product_name=product_name,
                        shop_name=shop.shop_name,
                        product_url=product_url,
                        price=price,
                        sales_est_min=sales_min,
                        sales_est_max=sales_max,
                        revenue_est_min=price * sales_min * 0.7,
                        revenue_est_max=price * sales_max,
                        score_winner=score,
                        category=random.choice(CATEGORIES),
                        last_scraped_at=datetime.utcnow() - timedelta(hours=random.randint(0, 72))
                    )
                    db.add(product)
                    products_created += 1
        
        db.commit()
        print(f"✅ {products_created} nouveaux produits créés")
        print()
        
        # Statistiques finales
        total_shops = db.query(ShopGlobal).count()
        total_products = db.query(ProductGlobal).count()
        total_winners = db.query(ProductGlobal).filter(ProductGlobal.score_winner >= 70).count()
        from sqlalchemy import func
        avg_score = db.query(func.avg(ProductGlobal.score_winner)).scalar() or 0
        
        print("="*70)
        print("📊 STATISTIQUES FINALES")
        print("="*70)
        print(f"🏪 Total boutiques: {total_shops}")
        print(f"📦 Total produits: {total_products}")
        print(f"⭐ Produits winners (score >= 70): {total_winners}")
        print(f"📈 Score moyen: {avg_score:.1f}/100")
        print()
        
        # Par marketplace
        for marketplace in ["chariow", "maketou"]:
            shops_count = db.query(ShopGlobal).filter(ShopGlobal.marketplace == marketplace).count()
            products_count = db.query(ProductGlobal).filter(ProductGlobal.marketplace == marketplace).count()
            print(f"   {marketplace.upper()}: {shops_count} boutiques, {products_count} produits")
        
        print()
        print("✅ Génération terminée!")
        
    finally:
        db.close()

if __name__ == "__main__":
    generate_test_data()

