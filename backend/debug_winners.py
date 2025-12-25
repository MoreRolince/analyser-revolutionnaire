"""
Script de diagnostic pour comprendre pourquoi aucune boutique winner n'est retournée
"""
from app.database import SessionLocal
from app.models import DigitalProductDetected, DigitalProductScore
from sqlalchemy import func

db = SessionLocal()

try:
    print("=" * 70)
    print("🔍 DIAGNOSTIC BOUTIQUES WINNERS")
    print("=" * 70)
    
    # 1. Nombre total de produits détectés
    total_products = db.query(func.count(DigitalProductDetected.id)).scalar()
    print(f"\n1️⃣ Total produits détectés (DigitalProductDetected): {total_products}")
    
    # 2. Nombre de produits avec un score
    products_with_score = db.query(func.count(DigitalProductDetected.id)).join(
        DigitalProductScore, DigitalProductDetected.id == DigitalProductScore.product_id
    ).scalar()
    print(f"2️⃣ Produits avec un score (jointure DigitalProductScore): {products_with_score}")
    
    # 3. Nombre de produits avec score >= 50
    products_score_50_plus = db.query(func.count(DigitalProductDetected.id)).join(
        DigitalProductScore, DigitalProductDetected.id == DigitalProductScore.product_id
    ).filter(DigitalProductScore.winner_score >= 50).scalar()
    print(f"3️⃣ Produits avec score >= 50: {products_score_50_plus}")
    
    # 4. Distribution des scores
    print(f"\n4️⃣ Distribution des scores:")
    score_ranges = [
        (0, 49, "0-49"),
        (50, 69, "50-69"),
        (70, 84, "70-84"),
        (85, 100, "85-100")
    ]
    for min_score, max_score, label in score_ranges:
        count = db.query(func.count(DigitalProductDetected.id)).join(
            DigitalProductScore, DigitalProductDetected.id == DigitalProductScore.product_id
        ).filter(
            DigitalProductScore.winner_score >= min_score,
            DigitalProductScore.winner_score <= max_score
        ).scalar()
        print(f"   - {label}: {count} produits")
    
    # 5. Produits avec seller_name NULL ou vide
    products_no_seller = db.query(func.count(DigitalProductDetected.id)).filter(
        (DigitalProductDetected.seller_name.is_(None)) | 
        (DigitalProductDetected.seller_name == '')
    ).scalar()
    print(f"\n5️⃣ Produits avec seller_name NULL ou vide: {products_no_seller}")
    
    # 6. Produits avec seller_name rempli ET score >= 50
    products_valid = db.query(func.count(DigitalProductDetected.id)).join(
        DigitalProductScore, DigitalProductDetected.id == DigitalProductScore.product_id
    ).filter(
        DigitalProductScore.winner_score >= 50,
        DigitalProductDetected.seller_name.isnot(None),
        DigitalProductDetected.seller_name != '',
        DigitalProductDetected.marketplace.isnot(None),
        DigitalProductDetected.marketplace != ''
    ).scalar()
    print(f"6️⃣ Produits valides (score >= 50, seller_name & marketplace remplis): {products_valid}")
    
    # 7. Top seller_name avec produits score >= 50
    print(f"\n7️⃣ Top 10 seller_name avec produits (score >= 50):")
    top_sellers = db.query(
        DigitalProductDetected.seller_name,
        DigitalProductDetected.marketplace,
        func.count(DigitalProductDetected.id).label('count')
    ).join(
        DigitalProductScore, DigitalProductDetected.id == DigitalProductScore.product_id
    ).filter(
        DigitalProductScore.winner_score >= 50,
        DigitalProductDetected.seller_name.isnot(None),
        DigitalProductDetected.seller_name != ''
    ).group_by(
        DigitalProductDetected.seller_name,
        DigitalProductDetected.marketplace
    ).order_by(func.count(DigitalProductDetected.id).desc()).limit(10).all()
    
    for seller, marketplace, count in top_sellers:
        print(f"   - {seller} ({marketplace}): {count} produit(s)")
    
    # 8. Boutiques avec au moins 2 produits (score >= 50)
    shops_with_2_plus = db.query(
        DigitalProductDetected.seller_name,
        DigitalProductDetected.marketplace,
        func.count(DigitalProductDetected.id).label('count'),
        func.avg(DigitalProductScore.winner_score).label('avg_score')
    ).join(
        DigitalProductScore, DigitalProductDetected.id == DigitalProductScore.product_id
    ).filter(
        DigitalProductScore.winner_score >= 50,
        DigitalProductDetected.seller_name.isnot(None),
        DigitalProductDetected.seller_name != '',
        DigitalProductDetected.marketplace.isnot(None),
        DigitalProductDetected.marketplace != ''
    ).group_by(
        DigitalProductDetected.seller_name,
        DigitalProductDetected.marketplace
    ).having(
        func.count(DigitalProductDetected.id) >= 2
    ).all()
    
    print(f"\n8️⃣ Boutiques avec >= 2 produits (score >= 50): {len(shops_with_2_plus)}")
    for seller, marketplace, count, avg_score in shops_with_2_plus[:5]:
        print(f"   - {seller} ({marketplace}): {count} produits, score moyen: {avg_score:.1f}")
    
    # 9. Exemples de produits avec score >= 50
    print(f"\n9️⃣ Exemples de produits avec score >= 50:")
    sample_products = db.query(
        DigitalProductDetected.seller_name,
        DigitalProductDetected.marketplace,
        DigitalProductDetected.product_title,
        DigitalProductScore.winner_score
    ).join(
        DigitalProductScore, DigitalProductDetected.id == DigitalProductScore.product_id
    ).filter(
        DigitalProductScore.winner_score >= 50
    ).limit(5).all()
    
    for seller, marketplace, title, score in sample_products:
        print(f"   - {title[:50]}...")
        print(f"     Seller: {seller}, Marketplace: {marketplace}, Score: {score}")
    
    print("\n" + "=" * 70)
    print("✅ Diagnostic terminé")
    print("=" * 70)
    
except Exception as e:
    print(f"❌ Erreur: {e}")
    import traceback
    traceback.print_exc()
finally:
    db.close()
