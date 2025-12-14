from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_
from typing import List, Optional
from datetime import datetime

from app.database import get_db
from app.models import ProductGlobal, ShopGlobal, MarketplaceType
from app.schemas import ProductGlobalResponse, ShopGlobalResponse
from app.auth import get_current_active_user

router = APIRouter()

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
    """Récupère les produits winners avec filtres - UNIQUEMENT les produits complets"""
    query = db.query(ProductGlobal)
    
    # FILTRE CRITIQUE: Uniquement les produits avec URL et nom (l'image est optionnelle)
    query = query.filter(
        ProductGlobal.product_url.isnot(None),
        ProductGlobal.product_url != '',
        ProductGlobal.product_name.isnot(None),
        ProductGlobal.product_name != ''
    )
    
    # Appliquer les filtres
    if marketplace:
        # Le marketplace est maintenant une string dans la base
        query = query.filter(ProductGlobal.marketplace == marketplace.lower())
    
    if min_score is not None:
        query = query.filter(ProductGlobal.score_winner >= min_score)
    
    if max_price is not None:
        query = query.filter(ProductGlobal.price <= max_price)
    
    if category:
        query = query.filter(ProductGlobal.category.ilike(f"%{category}%"))
    
    # Trier par score décroissant
    products = query.order_by(ProductGlobal.score_winner.desc()).offset(skip).limit(limit).all()
    
    # Convertir les produits en dictionnaires pour éviter les problèmes d'enum
    products_list = []
    for p in products:
        # Convertir marketplace en string (peut être enum ou string)
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
            created_at=p.created_at if hasattr(p, 'created_at') else datetime.now()
        ))
    
    # Ne retourner des données par défaut QUE si vraiment aucune donnée en base
    total_in_db = db.query(ProductGlobal).count()
    if not products_list and skip == 0 and total_in_db == 0:
        from datetime import datetime
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
                last_scraped_at=datetime.now(),
                created_at=datetime.now()
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
                last_scraped_at=datetime.now(),
                created_at=datetime.now()
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
                last_scraped_at=datetime.now(),
                created_at=datetime.now()
            )
        ][:limit]
    
    return products_list

@router.get("/products/{product_id}", response_model=ProductGlobalResponse)
async def get_winner_product(
    product_id: int,
    current_user = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Récupère un produit winner spécifique"""
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
        created_at=product.created_at if hasattr(product, 'created_at') else datetime.now()
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
    """Récupère les boutiques winners avec filtres - UNIQUEMENT les boutiques complètes"""
    query = db.query(ShopGlobal)
    
    # FILTRE CRITIQUE: Uniquement les boutiques complètes (URL, nom)
    query = query.filter(
        ShopGlobal.shop_url.isnot(None),
        ShopGlobal.shop_url != '',
        ShopGlobal.shop_name.isnot(None),
        ShopGlobal.shop_name != ''
    )
    
    # Appliquer les filtres
    if marketplace:
        # Le marketplace est maintenant une string dans la base
        query = query.filter(ShopGlobal.marketplace == marketplace.lower())
    
    if min_score is not None:
        query = query.filter(ShopGlobal.score_global >= min_score)
    
    if min_revenue is not None:
        query = query.filter(
            or_(
                ShopGlobal.revenue_est_min >= min_revenue,
                ShopGlobal.revenue_est_max >= min_revenue
            )
        )
    
    # Trier par score décroissant
    shops = query.order_by(ShopGlobal.score_global.desc()).offset(skip).limit(limit).all()
    
    # Convertir les boutiques en dictionnaires pour éviter les problèmes d'enum
    shops_list = []
    for s in shops:
        # Convertir marketplace en string (peut être enum ou string)
        if isinstance(s.marketplace, str):
            marketplace_str = s.marketplace
        elif hasattr(s.marketplace, 'value'):
            marketplace_str = s.marketplace.value
        else:
            marketplace_str = str(s.marketplace)
        shops_list.append(ShopGlobalResponse(
            id=s.id,
            marketplace=marketplace_str,
            shop_name=s.shop_name,
            shop_url=s.shop_url,
            score_global=s.score_global,
            revenue_est_min=s.revenue_est_min,
            revenue_est_max=s.revenue_est_max,
            winners_count=s.winners_count,
            last_scraped_at=s.last_scraped_at,
            created_at=s.created_at if hasattr(s, 'created_at') else datetime.now()
        ))
    
    # Ne retourner des données par défaut QUE si vraiment aucune donnée en base
    total_shops_in_db = db.query(ShopGlobal).count()
    if not shops_list and skip == 0 and total_shops_in_db == 0:
        from datetime import datetime
        return [
            ShopGlobalResponse(
                id=1,
                marketplace="chariow",
                shop_name="Boutique Winner Exemple 1",
                shop_url="https://example.com/shop1",
                score_global=90.3,
                revenue_est_min=2000000.0,
                revenue_est_max=5000000.0,
                winners_count=15,
                last_scraped_at=datetime.now(),
                created_at=datetime.now()
            ),
            ShopGlobalResponse(
                id=2,
                marketplace="maketou",
                shop_name="Boutique Winner Exemple 2",
                shop_url="https://example.com/shop2",
                score_global=87.8,
                revenue_est_min=1500000.0,
                revenue_est_max=4000000.0,
                winners_count=12,
                last_scraped_at=datetime.now(),
                created_at=datetime.now()
            ),
            ShopGlobalResponse(
                id=3,
                marketplace="systemeio",
                shop_name="Boutique Winner Exemple 3",
                shop_url="https://example.com/shop3",
                score_global=84.1,
                revenue_est_min=1000000.0,
                revenue_est_max=3000000.0,
                winners_count=8,
                last_scraped_at=datetime.now(),
                created_at=datetime.now()
            )
        ][:limit]
    
    return shops_list

@router.get("/shops/{shop_id}", response_model=ShopGlobalResponse)
async def get_winner_shop(
    shop_id: int,
    current_user = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Récupère une boutique winner spécifique"""
    shop = db.query(ShopGlobal).filter(ShopGlobal.id == shop_id).first()
    if not shop:
        raise HTTPException(status_code=404, detail="Shop not found")
    
    # Convertir en format de réponse
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
        created_at=shop.created_at if hasattr(shop, 'created_at') else datetime.now()
    )

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
        created_at=shop.created_at if hasattr(shop, 'created_at') else datetime.now()
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
        func.sum(func.case(
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


from sqlalchemy import and_, or_
from typing import List, Optional
from datetime import datetime

from app.database import get_db
from app.models import ProductGlobal, ShopGlobal, MarketplaceType
from app.schemas import ProductGlobalResponse, ShopGlobalResponse
from app.auth import get_current_active_user

router = APIRouter()

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
    """Récupère les produits winners avec filtres - UNIQUEMENT les produits complets"""
    query = db.query(ProductGlobal)
    
    # FILTRE CRITIQUE: Uniquement les produits avec URL et nom (l'image est optionnelle)
    query = query.filter(
        ProductGlobal.product_url.isnot(None),
        ProductGlobal.product_url != '',
        ProductGlobal.product_name.isnot(None),
        ProductGlobal.product_name != ''
    )
    
    # Appliquer les filtres
    if marketplace:
        # Le marketplace est maintenant une string dans la base
        query = query.filter(ProductGlobal.marketplace == marketplace.lower())
    
    if min_score is not None:
        query = query.filter(ProductGlobal.score_winner >= min_score)
    
    if max_price is not None:
        query = query.filter(ProductGlobal.price <= max_price)
    
    if category:
        query = query.filter(ProductGlobal.category.ilike(f"%{category}%"))
    
    # Trier par score décroissant
    products = query.order_by(ProductGlobal.score_winner.desc()).offset(skip).limit(limit).all()
    
    # Convertir les produits en dictionnaires pour éviter les problèmes d'enum
    products_list = []
    for p in products:
        # Convertir marketplace en string (peut être enum ou string)
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
            created_at=p.created_at if hasattr(p, 'created_at') else datetime.now()
        ))
    
    # Ne retourner des données par défaut QUE si vraiment aucune donnée en base
    total_in_db = db.query(ProductGlobal).count()
    if not products_list and skip == 0 and total_in_db == 0:
        from datetime import datetime
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
                last_scraped_at=datetime.now(),
                created_at=datetime.now()
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
                last_scraped_at=datetime.now(),
                created_at=datetime.now()
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
                last_scraped_at=datetime.now(),
                created_at=datetime.now()
            )
        ][:limit]
    
    return products_list

@router.get("/products/{product_id}", response_model=ProductGlobalResponse)
async def get_winner_product(
    product_id: int,
    current_user = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Récupère un produit winner spécifique"""
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
        created_at=product.created_at if hasattr(product, 'created_at') else datetime.now()
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
    """Récupère les boutiques winners avec filtres - UNIQUEMENT les boutiques complètes"""
    query = db.query(ShopGlobal)
    
    # FILTRE CRITIQUE: Uniquement les boutiques complètes (URL, nom)
    query = query.filter(
        ShopGlobal.shop_url.isnot(None),
        ShopGlobal.shop_url != '',
        ShopGlobal.shop_name.isnot(None),
        ShopGlobal.shop_name != ''
    )
    
    # Appliquer les filtres
    if marketplace:
        # Le marketplace est maintenant une string dans la base
        query = query.filter(ShopGlobal.marketplace == marketplace.lower())
    
    if min_score is not None:
        query = query.filter(ShopGlobal.score_global >= min_score)
    
    if min_revenue is not None:
        query = query.filter(
            or_(
                ShopGlobal.revenue_est_min >= min_revenue,
                ShopGlobal.revenue_est_max >= min_revenue
            )
        )
    
    # Trier par score décroissant
    shops = query.order_by(ShopGlobal.score_global.desc()).offset(skip).limit(limit).all()
    
    # Convertir les boutiques en dictionnaires pour éviter les problèmes d'enum
    shops_list = []
    for s in shops:
        # Convertir marketplace en string (peut être enum ou string)
        if isinstance(s.marketplace, str):
            marketplace_str = s.marketplace
        elif hasattr(s.marketplace, 'value'):
            marketplace_str = s.marketplace.value
        else:
            marketplace_str = str(s.marketplace)
        shops_list.append(ShopGlobalResponse(
            id=s.id,
            marketplace=marketplace_str,
            shop_name=s.shop_name,
            shop_url=s.shop_url,
            score_global=s.score_global,
            revenue_est_min=s.revenue_est_min,
            revenue_est_max=s.revenue_est_max,
            winners_count=s.winners_count,
            last_scraped_at=s.last_scraped_at,
            created_at=s.created_at if hasattr(s, 'created_at') else datetime.now()
        ))
    
    # Ne retourner des données par défaut QUE si vraiment aucune donnée en base
    total_shops_in_db = db.query(ShopGlobal).count()
    if not shops_list and skip == 0 and total_shops_in_db == 0:
        from datetime import datetime
        return [
            ShopGlobalResponse(
                id=1,
                marketplace="chariow",
                shop_name="Boutique Winner Exemple 1",
                shop_url="https://example.com/shop1",
                score_global=90.3,
                revenue_est_min=2000000.0,
                revenue_est_max=5000000.0,
                winners_count=15,
                last_scraped_at=datetime.now(),
                created_at=datetime.now()
            ),
            ShopGlobalResponse(
                id=2,
                marketplace="maketou",
                shop_name="Boutique Winner Exemple 2",
                shop_url="https://example.com/shop2",
                score_global=87.8,
                revenue_est_min=1500000.0,
                revenue_est_max=4000000.0,
                winners_count=12,
                last_scraped_at=datetime.now(),
                created_at=datetime.now()
            ),
            ShopGlobalResponse(
                id=3,
                marketplace="systemeio",
                shop_name="Boutique Winner Exemple 3",
                shop_url="https://example.com/shop3",
                score_global=84.1,
                revenue_est_min=1000000.0,
                revenue_est_max=3000000.0,
                winners_count=8,
                last_scraped_at=datetime.now(),
                created_at=datetime.now()
            )
        ][:limit]
    
    return shops_list

@router.get("/shops/{shop_id}", response_model=ShopGlobalResponse)
async def get_winner_shop(
    shop_id: int,
    current_user = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Récupère une boutique winner spécifique"""
    shop = db.query(ShopGlobal).filter(ShopGlobal.id == shop_id).first()
    if not shop:
        raise HTTPException(status_code=404, detail="Shop not found")
    
    # Convertir en format de réponse
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
        created_at=shop.created_at if hasattr(shop, 'created_at') else datetime.now()
    )

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
        created_at=shop.created_at if hasattr(shop, 'created_at') else datetime.now()
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
        func.sum(func.case(
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

