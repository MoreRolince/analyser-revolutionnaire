from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session, outerjoin
from sqlalchemy import and_, or_, desc, nullslast, case
from typing import List, Optional
from datetime import datetime as dt
import hashlib

from app.database import get_db
from app.models import ProductGlobal, ShopGlobal, MarketplaceType, DigitalProductDetected, DigitalProductScore
from app.schemas import ProductGlobalResponse, ShopGlobalResponse
from app.auth import get_current_active_user

router = APIRouter()

def generate_shop_id(domain: str, marketplace: str) -> int:
    """Génère un ID déterministe pour une boutique basé sur domaine + marketplace"""
    key = f"{domain}_{marketplace}"
    # Utiliser MD5 pour un hash déterministe, puis convertir en int
    hash_obj = hashlib.md5(key.encode('utf-8'))
    hash_hex = hash_obj.hexdigest()
    # Prendre les 9 premiers caractères hex et convertir en int, puis modulo 10^9
    return int(hash_hex[:9], 16) % (10**9)

@router.get("/products", response_model=List[ProductGlobalResponse])
async def get_winner_products(
    marketplace: Optional[str] = Query(None, description="Filter by marketplace"),
    min_score: Optional[float] = Query(None, ge=0, le=100, description="Minimum score"),
    max_price: Optional[float] = Query(None, ge=0, description="Maximum price"),
    category: Optional[str] = Query(None, description="Filter by category"),
    limit: int = Query(50, ge=1, le=1000, description="Number of results"),
    skip: int = Query(0, ge=0, description="Skip results"),
    current_user = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Récupère les produits winners depuis Facebook Ads - VRAIS produits scrapés"""
    from sqlalchemy.orm import outerjoin
    
    # Utiliser un LEFT JOIN pour inclure les produits même sans score
    # D'abord essayer de récupérer depuis DigitalProductDetected + DigitalProductScore (LEFT JOIN)
    query = db.query(DigitalProductDetected, DigitalProductScore).outerjoin(
        DigitalProductScore, DigitalProductDetected.id == DigitalProductScore.product_id
    )
    
    # Filtrer uniquement les produits winners crédibles
    # Ne jamais afficher les produits avec score = 0 (ils ne sont pas des winners)
    # Score minimum par défaut = 45 pour garantir la crédibilité (produits avec plusieurs annonces + bonne landing page)
    score_threshold = min_score if min_score is not None else 45.0
    
    # Filtrer les produits avec un score >= threshold (exclure les scores à 0 et NULL)
    query = query.filter(
        (DigitalProductScore.winner_score >= score_threshold) & (DigitalProductScore.winner_score.isnot(None))
    )
    
    # Appliquer les filtres
    if marketplace:
        query = query.filter(DigitalProductDetected.marketplace.ilike(f"%{marketplace.lower()}%"))
    
    if max_price is not None:
        query = query.filter(DigitalProductDetected.price <= max_price)
    
    if category:
        # Chercher dans le niche ou le product_type
        query = query.filter(
            or_(
                DigitalProductDetected.niche.ilike(f"%{category}%"),
                DigitalProductDetected.product_type.ilike(f"%{category}%")
            )
        )
    
    # Trier par score décroissant (NULLS LAST pour mettre les produits sans score à la fin)
    # Utiliser nullslast pour gérer les scores NULL
    results = query.order_by(
        nullslast(desc(DigitalProductScore.winner_score)),
        desc(DigitalProductDetected.created_at)
    ).offset(skip).limit(limit).all()
    
    # Convertir en format ProductGlobalResponse
    products_list = []
    for product, score in results:
        # Extraire l'image principale si disponible
        product_image = None
        if product.images and isinstance(product.images, list) and len(product.images) > 0:
            product_image = product.images[0]
        
        # Déterminer le shop_name (seller_name ou marketplace)
        shop_name = product.seller_name or product.marketplace or "Boutique"
        
        # Estimer les ventes basées sur le score et le prix
        # Estimation simple : plus le score est élevé, plus les ventes sont élevées
        # Si pas de score, utiliser des valeurs par défaut
        product_score = score.winner_score if score else 0.0
        sales_est_min = max(25, int(product_score * 0.5)) if product_score > 0 else 25
        sales_est_max = max(35, int(product_score * 0.7)) if product_score > 0 else 35
        
        # Calculer le revenue estimé
        revenue_est_min = (product.price or 0) * sales_est_min * 0.7 if product.price else None
        revenue_est_max = (product.price or 0) * sales_est_max if product.price else None
        
        # Utiliser le score si disponible, sinon 0
        score_value = score.winner_score if score else 0.0
        
        products_list.append(ProductGlobalResponse(
            id=product.id,
            marketplace=product.marketplace or "other",
            product_name=product.product_title,
            shop_name=shop_name,
            product_url=product.landing_page_url,
            product_image=product_image,
            product_description=product.description,
            price=product.price,
            sales_est_min=sales_est_min,
            sales_est_max=sales_est_max,
            revenue_est_min=revenue_est_min,
            revenue_est_max=revenue_est_max,
            score_winner=score_value,
            category=product.niche or product.product_type,
            last_scraped_at=product.analyzed_at,
            created_at=product.created_at
        ))
    
    # Si pas de produits depuis Facebook Ads, fallback sur ProductGlobal (pour compatibilité)
    if not products_list:
        query_fallback = db.query(ProductGlobal).filter(
            ProductGlobal.product_url.isnot(None),
            ProductGlobal.product_url != '',
            ProductGlobal.product_name.isnot(None),
            ProductGlobal.product_name != ''
        )
        
        if marketplace:
            query_fallback = query_fallback.filter(ProductGlobal.marketplace == marketplace.lower())
        
        if min_score is not None:
            query_fallback = query_fallback.filter(ProductGlobal.score_winner >= min_score)
        
        if max_price is not None:
            query_fallback = query_fallback.filter(ProductGlobal.price <= max_price)
        
        if category:
            query_fallback = query_fallback.filter(ProductGlobal.category.ilike(f"%{category}%"))
        
        products_fallback = query_fallback.order_by(ProductGlobal.score_winner.desc()).offset(skip).limit(limit).all()
        
        for p in products_fallback:
            if isinstance(p.marketplace, str):
                marketplace_str = p.marketplace
            elif hasattr(p.marketplace, 'value'):
                marketplace_str = p.marketplace.value
            else:
                marketplace_str = str(p.marketplace)
            products_list.append(ProductGlobalResponse(
                id=p.id,
                marketplace=marketplace_str,
                product_name=p.product_name,
                shop_name=p.shop_name,
                product_url=p.product_url,
                product_image=getattr(p, 'product_image', None),
                product_description=getattr(p, 'product_description', None),
                price=p.price,
                sales_est_min=p.sales_est_min,
                sales_est_max=p.sales_est_max,
                revenue_est_min=p.revenue_est_min,
                revenue_est_max=p.revenue_est_max,
                score_winner=p.score_winner,
                category=p.category,
                last_scraped_at=p.last_scraped_at,
                created_at=p.created_at if hasattr(p, 'created_at') else dt.now()
            ))
    
    # Ne retourner des données par défaut QUE si vraiment aucune donnée en base
    total_fb_ads = db.query(DigitalProductDetected).count()
    total_global = db.query(ProductGlobal).count()
    if not products_list and skip == 0 and total_fb_ads == 0 and total_global == 0:
        return [
            ProductGlobalResponse(
                id=1,
                marketplace="chariow",
                product_name="Produit Winner Exemple 1",
                shop_name="Boutique Exemple",
                product_url="https://example.com/product1",
                price=15000.0,
                sales_est_min=50,
                sales_est_max=150,
                revenue_est_min=750000.0,
                revenue_est_max=2250000.0,
                score_winner=88.5,
                category="Électronique",
                last_scraped_at=dt.now(),
                created_at=dt.now()
            ),
            ProductGlobalResponse(
                id=2,
                marketplace="maketou",
                product_name="Produit Winner Exemple 2",
                shop_name="Boutique Exemple 2",
                product_url="https://example.com/product2",
                price=25000.0,
                sales_est_min=30,
                sales_est_max=100,
                revenue_est_min=750000.0,
                revenue_est_max=2500000.0,
                score_winner=85.2,
                category="Mode",
                last_scraped_at=dt.now(),
                created_at=dt.now()
            ),
            ProductGlobalResponse(
                id=3,
                marketplace="systemeio",
                product_name="Produit Winner Exemple 3",
                shop_name="Boutique Exemple 3",
                product_url="https://example.com/product3",
                price=12000.0,
                sales_est_min=40,
                sales_est_max=120,
                revenue_est_min=480000.0,
                revenue_est_max=1440000.0,
                score_winner=82.7,
                category="Beauté",
                last_scraped_at=dt.now(),
                created_at=dt.now()
            )
        ][:limit]
    
    return products_list

@router.get("/products/{product_id}", response_model=ProductGlobalResponse)
async def get_winner_product(
    product_id: int,
    current_user = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Récupère un produit winner spécifique - Depuis Facebook Ads ou ProductGlobal"""
    # D'abord chercher dans DigitalProductDetected
    product = db.query(DigitalProductDetected).filter(DigitalProductDetected.id == product_id).first()
    score = None
    
    if product:
        score = db.query(DigitalProductScore).filter(DigitalProductScore.product_id == product.id).first()
        if score:
            # Extraire l'image principale
            product_image = None
            if product.images and isinstance(product.images, list) and len(product.images) > 0:
                product_image = product.images[0]
            
            shop_name = product.seller_name or product.marketplace or "Boutique"
            sales_est_min = max(25, int(score.winner_score * 0.5))
            sales_est_max = max(35, int(score.winner_score * 0.7))
            revenue_est_min = (product.price or 0) * sales_est_min * 0.7 if product.price else None
            revenue_est_max = (product.price or 0) * sales_est_max if product.price else None
            
            return ProductGlobalResponse(
                id=product.id,
                marketplace=product.marketplace or "other",
                product_name=product.product_title,
                shop_name=shop_name,
                product_url=product.landing_page_url,
                product_image=product_image,
                product_description=product.description,
                price=product.price,
                sales_est_min=sales_est_min,
                sales_est_max=sales_est_max,
                revenue_est_min=revenue_est_min,
                revenue_est_max=revenue_est_max,
                score_winner=score.winner_score,
                category=product.niche or product.product_type,
                last_scraped_at=product.analyzed_at,
                created_at=product.created_at
            )
    
    # Fallback sur ProductGlobal
    product = db.query(ProductGlobal).filter(ProductGlobal.id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    
    # Convertir en format de réponse
    marketplace_str = str(product.marketplace) if isinstance(product.marketplace, str) else (product.marketplace.value if hasattr(product.marketplace, 'value') else str(product.marketplace))
    
    return ProductGlobalResponse(
        id=product.id,
        marketplace=marketplace_str,
        product_name=product.product_name,
        shop_name=product.shop_name,
        product_url=product.product_url,
        product_image=getattr(product, 'product_image', None),
        product_description=getattr(product, 'product_description', None),
        price=product.price,
        sales_est_min=product.sales_est_min,
        sales_est_max=product.sales_est_max,
        revenue_est_min=product.revenue_est_min,
        revenue_est_max=product.revenue_est_max,
        score_winner=product.score_winner,
        category=product.category,
        last_scraped_at=product.last_scraped_at,
        created_at=product.created_at if hasattr(product, 'created_at') else dt.now()
    )

@router.get("/shops", response_model=List[ShopGlobalResponse])
async def get_winner_shops(
    marketplace: Optional[str] = Query(None, description="Filter by marketplace"),
    min_score: Optional[float] = Query(None, ge=0, le=100, description="Minimum score"),
    min_revenue: Optional[float] = Query(None, ge=0, description="Minimum revenue"),
    limit: int = Query(50, ge=1, le=1000, description="Number of results"),
    skip: int = Query(0, ge=0, description="Skip results"),
    current_user = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Récupère les boutiques winners depuis Facebook Ads - Agrégation des produits détectés"""
    from sqlalchemy import func
    from sqlalchemy.orm import outerjoin
    
    # Agréger les boutiques depuis DigitalProductDetected + DigitalProductScore
    # CRITÈRE STRICT: score >= 45 ET au moins 2 produits winners par boutique
    score_threshold = min_score if min_score is not None else 45.0
    
    try:
        
        # APPROCHE SIMPLIFIÉE: Récupérer tous les produits winners et grouper par domaine dans Python
        # C'est plus simple et plus fiable que d'essayer d'extraire le domaine dans SQL
        from urllib.parse import urlparse
        from collections import defaultdict
        
        # Récupérer tous les produits winners avec leurs URLs
        products_query = db.query(
            DigitalProductDetected.landing_page_url,
            DigitalProductDetected.marketplace,
            DigitalProductDetected.seller_name,
            DigitalProductScore.winner_score,
            DigitalProductDetected.price
        ).join(
            DigitalProductScore, DigitalProductDetected.id == DigitalProductScore.product_id
        ).filter(
            (DigitalProductScore.winner_score >= score_threshold) &
            (DigitalProductScore.winner_score.isnot(None)) &
            (DigitalProductDetected.marketplace.isnot(None)) &
            (DigitalProductDetected.marketplace != '') &
            (DigitalProductDetected.landing_page_url.isnot(None)) &
            (DigitalProductDetected.landing_page_url != '') &
            (DigitalProductDetected.landing_page_url.like('http%'))
        )
        
        # Appliquer les filtres
        if marketplace:
            products_query = products_query.filter(DigitalProductDetected.marketplace.ilike(f"%{marketplace.lower()}%"))
        
        all_products = products_query.all()
        
        # Grouper par domaine de base dans Python
        shops_dict = defaultdict(lambda: {
            'products': [],
            'marketplace': None,
            'seller_names': set(),
            'scores': [],
            'prices': []
        })
        
        for product in all_products:
            # Extraire le domaine de base depuis l'URL
            try:
                parsed = urlparse(product.landing_page_url)
                domain = parsed.netloc  # Ex: "ghost-tradyz.mychariow.shop"
                
                if not domain:
                    continue
                
                # Clé de groupement: domaine + marketplace
                shop_key = (domain, product.marketplace)
                shops_dict[shop_key]['products'].append(product.landing_page_url)
                shops_dict[shop_key]['marketplace'] = product.marketplace
                if product.seller_name:
                    shops_dict[shop_key]['seller_names'].add(product.seller_name)
                shops_dict[shop_key]['scores'].append(product.winner_score)
                if product.price:
                    shops_dict[shop_key]['prices'].append(product.price)
            except Exception as e:
                print(f"⚠️ Erreur extraction domaine pour {product.landing_page_url}: {e}")
                continue
        
        # Filtrer les boutiques avec >= 2 produits et construire les résultats
        # CRITÈRE STRICT: Au moins 2 produits winners par boutique
        results = []
        for (domain, marketplace_val), shop_data in shops_dict.items():
            products_count = len(shop_data['products'])
            if products_count >= 2:  # Au moins 2 produits winners (OBLIGATOIRE)
                avg_score = sum(shop_data['scores']) / len(shop_data['scores']) if shop_data['scores'] else 0
                min_price = min(shop_data['prices']) if shop_data['prices'] else None
                max_price = max(shop_data['prices']) if shop_data['prices'] else None
                revenue_est_min = sum(shop_data['prices']) * 30 if shop_data['prices'] else None
                revenue_est_max = sum(shop_data['prices']) * 50 if shop_data['prices'] else None
                seller_name = list(shop_data['seller_names'])[0] if shop_data['seller_names'] else ''
                sample_url = shop_data['products'][0]
                
                # Créer un objet similaire à row pour compatibilité
                from types import SimpleNamespace
                row = SimpleNamespace(
                    shop_domain=domain,
                    marketplace=marketplace_val,
                    sample_landing_url=sample_url,
                    seller_name=seller_name,
                    avg_score=avg_score,
                    winners_count=products_count,
                    min_price=min_price,
                    max_price=max_price,
                    revenue_est_min=revenue_est_min,
                    revenue_est_max=revenue_est_max
                )
                results.append(row)
        
        # Trier par score moyen décroissant puis par nombre de produits
        results.sort(key=lambda r: (r.avg_score, r.winners_count), reverse=True)
        results = results[skip:skip+limit]
        
    except Exception as e:
        # En cas d'erreur (par exemple pas de données), retourner une liste vide
        import traceback
        print(f"⚠️  Erreur dans get_winner_shops: {e}")
        traceback.print_exc()
        results = []
    
    # Convertir en format ShopGlobalResponse
    shops_list = []
    try:
        for row in results:
            # VÉRIFICATIONS STRICTES avant d'ajouter une boutique
            # 1. winners_count doit être >= 2 (OBLIGATOIRE - déjà filtré dans la boucle précédente)
            if not row.winners_count or row.winners_count < 2:
                print(f"⚠️  Boutique ignorée: seulement {row.winners_count or 0} produit(s) winner (< 2 requis)")
                continue
            
            # 2. shop_domain doit être valide
            shop_domain = row.shop_domain if hasattr(row, 'shop_domain') else None
            if not shop_domain:
                print(f"⚠️  Boutique ignorée: shop_domain vide")
                continue
            
            # shop_domain est déjà extrait et stocké dans row.shop_domain
            
            # 3. score moyen doit être >= threshold
            if not row.avg_score or row.avg_score < score_threshold:
                print(f"⚠️  Boutique {shop_domain} ignorée: score moyen {row.avg_score or 0} < {score_threshold}")
                continue
            
            # Extraire le nom de la boutique depuis le domaine (ex: ghost-tradyz.mychariow.shop -> Ghost Tradyz)
            # Pour Chariow/Maketou: prendre la partie avant le domaine principal
            if '.mychariow.shop' in shop_domain:
                shop_name_raw = shop_domain.replace('.mychariow.shop', '').replace('-', ' ').title()
            elif '.mymaketou.store' in shop_domain:
                shop_name_raw = shop_domain.replace('.mymaketou.store', '').replace('-', ' ').title()
            else:
                shop_name_raw = shop_domain.split('.')[0].replace('-', ' ').title()
            
            # Utiliser seller_name si disponible, sinon utiliser le nom extrait du domaine
            seller_name = row.seller_name if hasattr(row, 'seller_name') and row.seller_name and row.seller_name.strip() else None
            shop_name = seller_name or shop_name_raw or shop_domain
            
            # Construire l'URL de la boutique depuis shop_domain (déjà extrait)
            shop_url = None
            if shop_domain:
                try:
                    # shop_domain est déjà le domaine complet (ex: "ghost-tradyz.mychariow.shop")
                    # Construire l'URL selon la marketplace
                    if row.marketplace and 'chariow' in row.marketplace.lower():
                        # Pour Chariow: https://<nom>.mychariow.shop/fr
                        if '.mychariow.shop' in shop_domain:
                            shop_url = f"https://{shop_domain}/fr"
                        else:
                            print(f"⚠️ Domaine Chariow invalide pour {shop_name}: {shop_domain}")
                            continue
                    elif row.marketplace and 'maketou' in row.marketplace.lower():
                        # Pour Maketou: https://<nom>.mymaketou.store/fr
                        if '.mymaketou.store' in shop_domain:
                            shop_url = f"https://{shop_domain}/fr"
                        else:
                            print(f"⚠️ Domaine Maketou invalide pour {shop_name}: {shop_domain}")
                            continue
                    else:
                        # Pour les autres: utiliser le domaine de base
                        shop_url = f"https://{shop_domain}"
                except Exception as e:
                    print(f"⚠️ Erreur lors de la construction de l'URL de boutique pour {shop_name}: {e}")
                    continue
            
            # Si pas d'URL valide, sauter cette boutique
            if not shop_url:
                print(f"⚠️ Impossible de construire l'URL pour {shop_name} (shop_domain: {shop_domain}), boutique ignorée")
                continue
            
            # Filtrer par revenue si nécessaire
            if min_revenue is not None:
                if (row.revenue_est_min or 0) < min_revenue and (row.revenue_est_max or 0) < min_revenue:
                    continue
            
            # Générer un ID déterministe basé sur le domaine (clé unique pour identifier la boutique)
            marketplace_for_id = row.marketplace or "other"  # Utiliser "other" si None
            shop_id = generate_shop_id(shop_domain, marketplace_for_id)
            print(f"🏪 Ajout boutique: {shop_name} ({row.marketplace}) - Domain: {shop_domain} - ID: {shop_id}")
            shops_list.append(ShopGlobalResponse(
                id=shop_id,  # ID déterministe basé sur domaine + marketplace
                marketplace=row.marketplace or "other",
                shop_name=shop_name,
                shop_url=shop_url,
                score_global=float(row.avg_score) if row.avg_score else 0.0,
                revenue_est_min=float(row.revenue_est_min) if row.revenue_est_min else None,
                revenue_est_max=float(row.revenue_est_max) if row.revenue_est_max else None,
                winners_count=int(row.winners_count) if row.winners_count else 0,
                last_scraped_at=dt.now(),
                created_at=dt.now()
            ))
    except Exception as e:
        import traceback
        print(f"⚠️  Erreur lors de la conversion des boutiques: {e}")
        traceback.print_exc()
        shops_list = []  # Retourner une liste vide en cas d'erreur
    
    # NE PLUS UTILISER DE FALLBACK sur ShopGlobal
    # Les boutiques winners doivent TOUJOURS venir de DigitalProductDetected + DigitalProductScore
    # Cela garantit qu'on ne retourne que des boutiques qui ont vraiment au moins 2 produits winners (score >= 45)
    
    if not shops_list:
        print(f"ℹ️  Aucune boutique winner trouvée depuis Facebook Ads avec les critères:")
        print(f"   - Score >= {score_threshold}")
        print(f"   - Au moins 2 produits winners par boutique (OBLIGATOIRE)")
        print(f"   - seller_name et marketplace non vides")
        return []
    
    print(f"✅ Retour de {len(shops_list)} boutiques winners avec >= 2 produits depuis Facebook Ads")
    
    return shops_list

@router.get("/shops/{shop_id}", response_model=ShopGlobalResponse)
async def get_winner_shop(
    shop_id: int,
    current_user = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Récupère une boutique winner spécifique - Utilise la même logique que get_winner_shops"""
    from sqlalchemy import func
    from urllib.parse import urlparse
    from collections import defaultdict
    
    # Utiliser la MÊME logique que get_winner_shops pour trouver la boutique
    score_threshold = 45.0
    
    # Récupérer tous les produits winners et grouper par domaine (comme dans get_winner_shops)
    products_query = db.query(
        DigitalProductDetected.landing_page_url,
        DigitalProductDetected.marketplace,
        DigitalProductDetected.seller_name,
        DigitalProductScore.winner_score,
        DigitalProductDetected.price
    ).join(
        DigitalProductScore, DigitalProductDetected.id == DigitalProductScore.product_id
    ).filter(
        (DigitalProductScore.winner_score >= score_threshold) &
        (DigitalProductScore.winner_score.isnot(None)) &
        (DigitalProductDetected.marketplace.isnot(None)) &
        (DigitalProductDetected.marketplace != '') &
        (DigitalProductDetected.landing_page_url.isnot(None)) &
        (DigitalProductDetected.landing_page_url != '') &
        (DigitalProductDetected.landing_page_url.like('http%'))
    )
    
    all_products = products_query.all()
    
    # Grouper par domaine (MÊME logique que get_winner_shops)
    shops_dict = defaultdict(lambda: {
        'products': [],
        'marketplace': None,
        'seller_names': set(),
        'scores': [],
        'prices': []
    })
    
    for product in all_products:
        try:
            parsed = urlparse(product.landing_page_url)
            domain = parsed.netloc
            
            if not domain:
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
            continue
    
    # Trouver la boutique avec l'ID correspondant (MÊME logique de génération d'ID)
    shop_found = None
    print(f"🔍 Recherche boutique avec shop_id: {shop_id}")
    print(f"🔍 Nombre de boutiques candidates: {len([s for (d, m), s in shops_dict.items() if len(s['products']) >= 2])}")
    
    for (domain, marketplace_val), shop_data in shops_dict.items():
        products_count = len(shop_data['products'])
        if products_count >= 2:  # Au moins 2 produits
            # Générer l'ID de la même manière que dans get_winner_shops
            calculated_id = generate_shop_id(domain, marketplace_val)
            print(f"  📊 Boutique: {domain} ({marketplace_val}) - ID calculé: {calculated_id}, Produits: {products_count}")
            if calculated_id == shop_id:
                print(f"  ✅ Boutique trouvée! {domain} ({marketplace_val})")
                # Construire les données de la boutique trouvée
                avg_score = sum(shop_data['scores']) / len(shop_data['scores']) if shop_data['scores'] else 0
                min_price = min(shop_data['prices']) if shop_data['prices'] else None
                max_price = max(shop_data['prices']) if shop_data['prices'] else None
                revenue_est_min = sum(shop_data['prices']) * 30 if shop_data['prices'] else None
                revenue_est_max = sum(shop_data['prices']) * 50 if shop_data['prices'] else None
                seller_name = list(shop_data['seller_names'])[0] if shop_data['seller_names'] else ''
                sample_url = shop_data['products'][0]
                
                # Extraire le nom de la boutique depuis le domaine (même logique que get_winner_shops)
                if '.mychariow.shop' in domain:
                    shop_name_raw = domain.replace('.mychariow.shop', '').replace('-', ' ').title()
                elif '.mymaketou.store' in domain:
                    shop_name_raw = domain.replace('.mymaketou.store', '').replace('-', ' ').title()
                else:
                    shop_name_raw = domain.split('.')[0].replace('-', ' ').title()
                
                shop_name = seller_name or shop_name_raw or domain
                
                # Construire l'URL de la boutique
                shop_url = None
                if marketplace_val and 'chariow' in marketplace_val.lower():
                    if '.mychariow.shop' in domain:
                        shop_url = f"https://{domain}/fr"
                elif marketplace_val and 'maketou' in marketplace_val.lower():
                    if '.mymaketou.store' in domain:
                        shop_url = f"https://{domain}/fr"
                else:
                    shop_url = f"https://{domain}"
                
                if shop_url:
                    shop_found = {
                        'domain': domain,
                        'marketplace': marketplace_val,
                        'shop_name': shop_name,
                        'shop_url': shop_url,
                        'avg_score': avg_score,
                        'winners_count': products_count,
                        'revenue_est_min': revenue_est_min,
                        'revenue_est_max': revenue_est_max
                    }
                    break
    
    # Si trouvée, retourner la réponse
    if not shop_found:
        print(f"❌ Boutique non trouvée avec shop_id: {shop_id}")
        print(f"   Vérifier que l'ID correspond bien à une boutique avec >= 2 produits (score >= 45)")
    
    if shop_found:
        return ShopGlobalResponse(
            id=shop_id,
            marketplace=shop_found['marketplace'] or "other",
            shop_name=shop_found['shop_name'],
            shop_url=shop_found['shop_url'],
            score_global=float(shop_found['avg_score']),
            revenue_est_min=float(shop_found['revenue_est_min']) if shop_found['revenue_est_min'] else None,
            revenue_est_max=float(shop_found['revenue_est_max']) if shop_found['revenue_est_max'] else None,
            winners_count=int(shop_found['winners_count']),
            last_scraped_at=dt.now(),
            created_at=dt.now()
        )
    
    # Fallback: chercher dans ShopGlobal
    shop = db.query(ShopGlobal).filter(ShopGlobal.id == shop_id).first()
    if not shop:
        raise HTTPException(status_code=404, detail="Shop not found")
    
    marketplace_str = str(shop.marketplace) if isinstance(shop.marketplace, str) else (shop.marketplace.value if hasattr(shop.marketplace, 'value') else str(shop.marketplace))
    
    return ShopGlobalResponse(
        id=shop.id,
        marketplace=marketplace_str,
        shop_name=shop.shop_name,
        shop_url=shop.shop_url,
        score_global=shop.score_global,
        revenue_est_min=shop.revenue_est_min,
        revenue_est_max=shop.revenue_est_max,
        winners_count=shop.winners_count,
        last_scraped_at=shop.last_scraped_at,
        created_at=shop.created_at if hasattr(shop, 'created_at') else dt.now()
    )

@router.get("/shops/{shop_id}/products", response_model=List[ProductGlobalResponse])
async def get_winner_shop_products(
    shop_id: int,
    min_score: Optional[float] = Query(45.0, ge=0, le=100, description="Minimum score"),
    current_user = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Récupère les produits winners d'une boutique spécifique depuis DigitalProductDetected + DigitalProductScore"""
    from urllib.parse import urlparse
    from collections import defaultdict
    
    score_threshold = min_score if min_score is not None else 45.0
    
    # Récupérer tous les produits winners et grouper par domaine (MÊME logique que get_winner_shops)
    products_query = db.query(
        DigitalProductDetected.landing_page_url,
        DigitalProductDetected.marketplace,
        DigitalProductDetected.seller_name,
        DigitalProductDetected.id,
        DigitalProductDetected.product_title,
        DigitalProductDetected.price,
        DigitalProductDetected.images,
        DigitalProductDetected.description,
        DigitalProductDetected.created_at,
        DigitalProductDetected.analyzed_at,
        DigitalProductScore.winner_score
    ).join(
        DigitalProductScore, DigitalProductDetected.id == DigitalProductScore.product_id
    ).filter(
        (DigitalProductScore.winner_score >= score_threshold) &
        (DigitalProductScore.winner_score.isnot(None)) &
        (DigitalProductDetected.marketplace.isnot(None)) &
        (DigitalProductDetected.marketplace != '') &
        (DigitalProductDetected.landing_page_url.isnot(None)) &
        (DigitalProductDetected.landing_page_url != '') &
        (DigitalProductDetected.landing_page_url.like('http%'))
    )
    
    all_products = products_query.all()
    
    # Grouper par domaine (MÊME logique que get_winner_shops)
    shops_dict = defaultdict(lambda: {
        'products': [],
        'marketplace': None,
        'seller_names': set(),
        'scores': [],
        'prices': []
    })
    
    # Mapping pour stocker les produits par domaine
    products_by_domain = defaultdict(list)
    
    for product in all_products:
        try:
            parsed = urlparse(product.landing_page_url)
            domain = parsed.netloc
            
            if not domain:
                continue
            
            shop_key = (domain, product.marketplace)
            shops_dict[shop_key]['products'].append(product.landing_page_url)
            shops_dict[shop_key]['marketplace'] = product.marketplace
            if product.seller_name:
                shops_dict[shop_key]['seller_names'].add(product.seller_name)
            shops_dict[shop_key]['scores'].append(product.winner_score)
            if product.price:
                shops_dict[shop_key]['prices'].append(product.price)
            
            # Stocker le produit complet pour pouvoir le récupérer ensuite
            products_by_domain[shop_key].append(product)
        except Exception as e:
            continue
    
    # Trouver la boutique avec l'ID correspondant (MÊME logique de génération d'ID)
    target_domain = None
    target_marketplace = None
    
    for (domain, marketplace_val), shop_data in shops_dict.items():
        products_count = len(shop_data['products'])
        if products_count >= 2:  # Au moins 2 produits
            # Générer l'ID de la même manière que dans get_winner_shops
            calculated_id = generate_shop_id(domain, marketplace_val)
            if calculated_id == shop_id:
                target_domain = domain
                target_marketplace = marketplace_val
                break
    
    if not target_domain or not target_marketplace:
        raise HTTPException(status_code=404, detail="Shop not found or no products")
    
    # Récupérer les produits de cette boutique (filtrer par domaine dans l'URL)
    target_products = products_by_domain[(target_domain, target_marketplace)]
    
    # Convertir en format ProductGlobalResponse
    products_list = []
    for product in target_products:
        product_image = None
        if product.images and isinstance(product.images, list) and len(product.images) > 0:
            product_image = product.images[0]
        
        products_list.append(ProductGlobalResponse(
            id=product.id,
            marketplace=product.marketplace or "other",
            product_name=product.product_title or "Produit sans nom",
            shop_name=product.seller_name or "Boutique",
            product_url=product.landing_page_url,
            product_image=product_image,
            product_description=product.description,
            price=product.price,
            sales_est_min=30,  # Estimation par défaut
            sales_est_max=50,
            revenue_est_min=float(product.price * 30) if product.price else None,
            revenue_est_max=float(product.price * 50) if product.price else None,
            score_winner=float(product.winner_score) if product.winner_score else 0.0,
            category=None,  # Pas encore implémenté
            last_scraped_at=product.analyzed_at,
            created_at=product.created_at
        ))
    
    # Trier par score décroissant
    products_list.sort(key=lambda p: p.score_winner or 0, reverse=True)
    
    return products_list

@router.get("/shop-by-name")
async def get_shop_by_name(
    shop_name: str = Query(..., description="Shop name"),
    current_user = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Récupère une boutique par son nom (recherche insensible à la casse)"""
    # Essayer d'abord une recherche exacte (insensible à la casse)
    shop = db.query(ShopGlobal).filter(
        ShopGlobal.shop_name.ilike(shop_name.strip())
    ).first()
    
    # Si pas trouvé, essayer une recherche partielle
    if not shop:
        shop = db.query(ShopGlobal).filter(
            ShopGlobal.shop_name.ilike(f"%{shop_name.strip()}%")
        ).first()
    
    if not shop:
        raise HTTPException(status_code=404, detail=f"Shop not found: {shop_name}")
    
    marketplace_str = str(shop.marketplace) if isinstance(shop.marketplace, str) else (shop.marketplace.value if hasattr(shop.marketplace, 'value') else str(shop.marketplace))
    
    return ShopGlobalResponse(
        id=shop.id,
        marketplace=marketplace_str,
        shop_name=shop.shop_name,
        shop_url=shop.shop_url,
        score_global=shop.score_global,
        revenue_est_min=shop.revenue_est_min,
        revenue_est_max=shop.revenue_est_max,
        winners_count=shop.winners_count,
        last_scraped_at=shop.last_scraped_at,
        created_at=shop.created_at if hasattr(shop, 'created_at') else dt.now()
    )

@router.get("/categories")
async def get_categories(
    marketplace: Optional[str] = Query(None, description="Filter by marketplace"),
    current_user = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Récupère la liste des catégories disponibles"""
    query = db.query(ProductGlobal.category).distinct()
    
    if marketplace:
        # Le marketplace est maintenant une string dans la base
        query = query.filter(ProductGlobal.marketplace == marketplace.lower())
    
    categories = [cat[0] for cat in query.filter(ProductGlobal.category.isnot(None)).all() if cat[0]]
    return {"categories": sorted(categories)}

@router.get("/check-products")
async def check_products(
    current_user = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Vérifie les produits dans la base de données qui remplissent les conditions"""
    from sqlalchemy import func
    
    # Compter tous les produits
    total_products = db.query(ProductGlobal).count()
    
    # Produits avec nom ET URL (conditions minimales)
    products_with_name_and_url = db.query(ProductGlobal).filter(
        ProductGlobal.product_name.isnot(None),
        ProductGlobal.product_name != '',
        ProductGlobal.product_url.isnot(None),
        ProductGlobal.product_url != ''
    ).count()
    
    # Produits avec nom, URL ET image
    products_complete = db.query(ProductGlobal).filter(
        ProductGlobal.product_name.isnot(None),
        ProductGlobal.product_name != '',
        ProductGlobal.product_url.isnot(None),
        ProductGlobal.product_url != '',
        ProductGlobal.product_image.isnot(None),
        ProductGlobal.product_image != ''
    ).count()
    
    # Produits d'exemple
    example_products = db.query(ProductGlobal).filter(
        func.lower(ProductGlobal.product_name).contains('exemple')
    ).count()
    
    # Afficher les premiers produits valides
    valid_products = db.query(ProductGlobal).filter(
        ProductGlobal.product_name.isnot(None),
        ProductGlobal.product_name != '',
        ProductGlobal.product_url.isnot(None),
        ProductGlobal.product_url != ''
    ).order_by(ProductGlobal.id.desc()).limit(10).all()
    
    products_list = []
    for p in valid_products:
        has_image = p.product_image and p.product_image.strip() != ''
        products_list.append({
            "id": p.id,
            "name": p.product_name[:80],
            "url": p.product_url[:80],
            "has_image": has_image,
            "marketplace": str(p.marketplace),
            "score": p.score_winner,
            "price": p.price
        })
    
    # Statistiques par marketplace
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
    
    marketplace_data = [
        {
            "marketplace": str(mp),
            "total": total,
            "avec_nom_url": int(avec_nom_url) if avec_nom_url else 0
        }
        for mp, total, avec_nom_url in marketplace_stats
    ]
    
    return {
        "total_products": total_products,
        "products_with_name_and_url": products_with_name_and_url,
        "products_complete": products_complete,
        "example_products": example_products,
        "valid_products_count": products_with_name_and_url - example_products,
        "sample_products": products_list,
        "marketplace_stats": marketplace_data
    }

