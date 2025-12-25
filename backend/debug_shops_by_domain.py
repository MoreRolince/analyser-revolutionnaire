"""
Script de diagnostic pour vérifier le groupement par domaine
"""
from app.database import SessionLocal
from app.models import DigitalProductDetected, DigitalProductScore
from sqlalchemy import func
from urllib.parse import urlparse
from collections import defaultdict

db = SessionLocal()

try:
    print("=" * 70)
    print("🔍 DIAGNOSTIC GROUPEMENT PAR DOMAINE")
    print("=" * 70)
    
    # Récupérer tous les produits avec score >= 50
    products = db.query(
        DigitalProductDetected.landing_page_url,
        DigitalProductDetected.marketplace,
        DigitalProductDetected.seller_name,
        DigitalProductScore.winner_score,
        DigitalProductDetected.price
    ).join(
        DigitalProductScore, DigitalProductDetected.id == DigitalProductScore.product_id
    ).filter(
        (DigitalProductScore.winner_score >= 50) &
        (DigitalProductScore.winner_score.isnot(None)) &
        (DigitalProductDetected.marketplace.isnot(None)) &
        (DigitalProductDetected.marketplace != '') &
        (DigitalProductDetected.landing_page_url.isnot(None)) &
        (DigitalProductDetected.landing_page_url != '') &
        (DigitalProductDetected.landing_page_url.like('http%'))
    ).all()
    
    print(f"\n📦 Total produits avec score >= 50: {len(products)}")
    
    # Grouper par domaine
    shops_dict = defaultdict(lambda: {
        'products': [],
        'marketplace': None,
        'seller_names': set(),
        'scores': [],
        'prices': []
    })
    
    for product in products:
        try:
            parsed = urlparse(product.landing_page_url)
            domain = parsed.netloc  # Ex: "ghost-tradyz.mychariow.shop"
            
            if not domain:
                print(f"⚠️ Pas de domaine pour: {product.landing_page_url}")
                continue
            
            shop_key = (domain, product.marketplace)
            shops_dict[shop_key]['products'].append(product.landing_page_url)
            shops_dict[shop_key]['marketplace'] = product.marketplace
            if product.seller_name:
                shops_dict[shop_key]['seller_names'].add(product.seller_name)
            shops_dict[shop_key]['scores'].append(product.winner_score)
            if product.price:
                shops_dict[shop_key]['prices'].append(product.price)
        except Exception as e:
            print(f"⚠️ Erreur pour {product.landing_page_url}: {e}")
            continue
    
    print(f"\n🏪 Boutiques uniques (par domaine): {len(shops_dict)}")
    
    # Afficher les boutiques avec >= 2 produits
    shops_with_2_plus = {k: v for k, v in shops_dict.items() if len(v['products']) >= 2}
    print(f"\n✅ Boutiques avec >= 2 produits: {len(shops_with_2_plus)}")
    
    for (domain, marketplace), shop_data in shops_with_2_plus.items():
        print(f"\n  🏪 {domain} ({marketplace})")
        print(f"     Produits: {len(shop_data['products'])}")
        print(f"     Scores: {shop_data['scores']}")
        print(f"     Seller names: {list(shop_data['seller_names'])}")
        print(f"     URLs produits:")
        for url in shop_data['products'][:3]:
            print(f"       - {url}")
    
    # Afficher quelques exemples de produits pour comprendre la structure
    print(f"\n📋 Exemples de produits (premiers 5):")
    for i, product in enumerate(products[:5]):
        parsed = urlparse(product.landing_page_url)
        domain = parsed.netloc
        print(f"  {i+1}. {domain} | {product.marketplace} | {product.seller_name} | Score: {product.winner_score}")
        print(f"     URL: {product.landing_page_url}")
    
    print("\n" + "=" * 70)
    print("✅ Diagnostic terminé")
    print("=" * 70)
    
except Exception as e:
    print(f"❌ Erreur: {e}")
    import traceback
    traceback.print_exc()
finally:
    db.close()
