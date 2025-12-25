"""
Script pour vérifier les produits dans la base de données
"""
import sys
import os

# Ajouter le répertoire backend au path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.database import SessionLocal
from app.models import ProductGlobal
from sqlalchemy import func, case

def check_products():
    db = SessionLocal()
    try:
        # Compter tous les produits
        total_products = db.query(ProductGlobal).count()
        print(f"\n{'='*60}")
        print(f"VÉRIFICATION DES PRODUITS DANS LA BASE DE DONNÉES")
        print(f"{'='*60}\n")
        print(f"Total de produits dans la base: {total_products}\n")
        
        # Produits avec nom ET URL (conditions minimales)
        products_with_name_and_url = db.query(ProductGlobal).filter(
            ProductGlobal.product_name.isnot(None),
            ProductGlobal.product_name != '',
            ProductGlobal.product_url.isnot(None),
            ProductGlobal.product_url != ''
        ).count()
        print(f"Produits avec nom ET URL: {products_with_name_and_url}")
        
        # Produits avec nom, URL ET image
        products_complete = db.query(ProductGlobal).filter(
            ProductGlobal.product_name.isnot(None),
            ProductGlobal.product_name != '',
            ProductGlobal.product_url.isnot(None),
            ProductGlobal.product_url != '',
            ProductGlobal.product_image.isnot(None),
            ProductGlobal.product_image != ''
        ).count()
        print(f"Produits avec nom, URL ET image: {products_complete}\n")
        
        # Afficher les premiers produits qui remplissent les conditions
        print(f"{'='*60}")
        print(f"PREMIERS PRODUITS AVEC NOM ET URL (max 20):")
        print(f"{'='*60}\n")
        
        valid_products = db.query(ProductGlobal).filter(
            ProductGlobal.product_name.isnot(None),
            ProductGlobal.product_name != '',
            ProductGlobal.product_url.isnot(None),
            ProductGlobal.product_url != ''
        ).order_by(ProductGlobal.id.desc()).limit(20).all()
        
        if valid_products:
            for i, product in enumerate(valid_products, 1):
                has_image = product.product_image and product.product_image.strip() != ''
                image_status = "✓" if has_image else "✗"
                print(f"{i}. ID: {product.id}")
                print(f"   Nom: {product.product_name[:60]}...")
                print(f"   URL: {product.product_url[:60]}...")
                print(f"   Image: {image_status} {'(présente)' if has_image else '(manquante)'}")
                print(f"   Marketplace: {product.marketplace}")
                print(f"   Score: {product.score_winner if product.score_winner else 'N/A'}")
                print(f"   Prix: {product.price if product.price else 'N/A'} FCFA")
                print()
        else:
            print("Aucun produit trouvé avec nom et URL !\n")
        
        # Statistiques par marketplace
        print(f"{'='*60}")
        print(f"STATISTIQUES PAR MARKETPLACE:")
        print(f"{'='*60}\n")
        
        marketplace_stats = db.query(
            ProductGlobal.marketplace,
            func.count(ProductGlobal.id).label('total'),
            func.sum(case(
                (
                    (ProductGlobal.product_name.isnot(None)) & 
                    (ProductGlobal.product_name != '') &
                    (ProductGlobal.product_url.isnot(None)) &
                    (ProductGlobal.product_url != ''),
                    1
                ),
                else_=0
            )).label('avec_nom_url')
        ).group_by(ProductGlobal.marketplace).all()
        
        for marketplace, total, avec_nom_url in marketplace_stats:
            print(f"{marketplace}:")
            print(f"  Total: {total}")
            print(f"  Avec nom + URL: {avec_nom_url}")
            print()
        
        # Produits d'exemple à exclure
        print(f"{'='*60}")
        print(f"PRODUITS D'EXEMPLE (à exclure):")
        print(f"{'='*60}\n")
        
        example_products = db.query(ProductGlobal).filter(
            func.lower(ProductGlobal.product_name).contains('exemple')
        ).all()
        
        if example_products:
            for product in example_products:
                print(f"  - ID {product.id}: {product.product_name}")
        else:
            print("  Aucun produit d'exemple trouvé\n")
        
        # Résumé final
        print(f"{'='*60}")
        print(f"RÉSUMÉ:")
        print(f"{'='*60}\n")
        print(f"Produits affichables (nom + URL, sans 'exemple'): {products_with_name_and_url - len(example_products)}")
        print(f"Produits complets (nom + URL + image, sans 'exemple'): {products_complete - len([p for p in example_products if p.product_image])}")
        print()
        
    except Exception as e:
        print(f"Erreur: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    check_products()

"""
Script pour vérifier les produits dans la base de données
"""
import sys
import os

# Ajouter le répertoire backend au path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.database import SessionLocal
from app.models import ProductGlobal
from sqlalchemy import func, case

def check_products():
    db = SessionLocal()
    try:
        # Compter tous les produits
        total_products = db.query(ProductGlobal).count()
        print(f"\n{'='*60}")
        print(f"VÉRIFICATION DES PRODUITS DANS LA BASE DE DONNÉES")
        print(f"{'='*60}\n")
        print(f"Total de produits dans la base: {total_products}\n")
        
        # Produits avec nom ET URL (conditions minimales)
        products_with_name_and_url = db.query(ProductGlobal).filter(
            ProductGlobal.product_name.isnot(None),
            ProductGlobal.product_name != '',
            ProductGlobal.product_url.isnot(None),
            ProductGlobal.product_url != ''
        ).count()
        print(f"Produits avec nom ET URL: {products_with_name_and_url}")
        
        # Produits avec nom, URL ET image
        products_complete = db.query(ProductGlobal).filter(
            ProductGlobal.product_name.isnot(None),
            ProductGlobal.product_name != '',
            ProductGlobal.product_url.isnot(None),
            ProductGlobal.product_url != '',
            ProductGlobal.product_image.isnot(None),
            ProductGlobal.product_image != ''
        ).count()
        print(f"Produits avec nom, URL ET image: {products_complete}\n")
        
        # Afficher les premiers produits qui remplissent les conditions
        print(f"{'='*60}")
        print(f"PREMIERS PRODUITS AVEC NOM ET URL (max 20):")
        print(f"{'='*60}\n")
        
        valid_products = db.query(ProductGlobal).filter(
            ProductGlobal.product_name.isnot(None),
            ProductGlobal.product_name != '',
            ProductGlobal.product_url.isnot(None),
            ProductGlobal.product_url != ''
        ).order_by(ProductGlobal.id.desc()).limit(20).all()
        
        if valid_products:
            for i, product in enumerate(valid_products, 1):
                has_image = product.product_image and product.product_image.strip() != ''
                image_status = "✓" if has_image else "✗"
                print(f"{i}. ID: {product.id}")
                print(f"   Nom: {product.product_name[:60]}...")
                print(f"   URL: {product.product_url[:60]}...")
                print(f"   Image: {image_status} {'(présente)' if has_image else '(manquante)'}")
                print(f"   Marketplace: {product.marketplace}")
                print(f"   Score: {product.score_winner if product.score_winner else 'N/A'}")
                print(f"   Prix: {product.price if product.price else 'N/A'} FCFA")
                print()
        else:
            print("Aucun produit trouvé avec nom et URL !\n")
        
        # Statistiques par marketplace
        print(f"{'='*60}")
        print(f"STATISTIQUES PAR MARKETPLACE:")
        print(f"{'='*60}\n")
        
        marketplace_stats = db.query(
            ProductGlobal.marketplace,
            func.count(ProductGlobal.id).label('total'),
            func.sum(case(
                (
                    (ProductGlobal.product_name.isnot(None)) & 
                    (ProductGlobal.product_name != '') &
                    (ProductGlobal.product_url.isnot(None)) &
                    (ProductGlobal.product_url != ''),
                    1
                ),
                else_=0
            )).label('avec_nom_url')
        ).group_by(ProductGlobal.marketplace).all()
        
        for marketplace, total, avec_nom_url in marketplace_stats:
            print(f"{marketplace}:")
            print(f"  Total: {total}")
            print(f"  Avec nom + URL: {avec_nom_url}")
            print()
        
        # Produits d'exemple à exclure
        print(f"{'='*60}")
        print(f"PRODUITS D'EXEMPLE (à exclure):")
        print(f"{'='*60}\n")
        
        example_products = db.query(ProductGlobal).filter(
            func.lower(ProductGlobal.product_name).contains('exemple')
        ).all()
        
        if example_products:
            for product in example_products:
                print(f"  - ID {product.id}: {product.product_name}")
        else:
            print("  Aucun produit d'exemple trouvé\n")
        
        # Résumé final
        print(f"{'='*60}")
        print(f"RÉSUMÉ:")
        print(f"{'='*60}\n")
        print(f"Produits affichables (nom + URL, sans 'exemple'): {products_with_name_and_url - len(example_products)}")
        print(f"Produits complets (nom + URL + image, sans 'exemple'): {products_complete - len([p for p in example_products if p.product_image])}")
        print()
        
    except Exception as e:
        print(f"Erreur: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    check_products()

