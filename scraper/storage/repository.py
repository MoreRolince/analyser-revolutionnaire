"""Repository utilitaire pour persister shops/produits et snapshots."""
from __future__ import annotations

import os
from datetime import datetime, date
from typing import Optional

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

# Import des modèles backend (ProductGlobal / ShopGlobal)
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
BACKEND_PATH = PROJECT_ROOT / "backend"
if str(BACKEND_PATH) not in sys.path:
    sys.path.insert(0, str(BACKEND_PATH))

from app.models import ProductGlobal, ShopGlobal  # type: ignore


DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://marketpulse:marketpulse_password@localhost:5433/marketpulse",
)

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(bind=engine)


def ensure_snapshot_tables():
    """Crée des tables de snapshots si elles n'existent pas (compatibilité sans migration)."""
    with engine.begin() as conn:
        conn.execute(
            text(
                """
                CREATE TABLE IF NOT EXISTS product_snapshots_global (
                  id SERIAL PRIMARY KEY,
                  product_url TEXT NOT NULL,
                  snapshot_date DATE DEFAULT CURRENT_DATE,
                  winner_score NUMERIC,
                  growth_index NUMERIC,
                  popularity_index NUMERIC,
                  competition_index NUMERIC,
                  potential_index NUMERIC,
                  review_growth NUMERIC,
                  price NUMERIC,
                  ranking_position INT,
                  number_of_reviews INT,
                  created_at TIMESTAMPTZ DEFAULT now()
                );
                """
            )
        )
        conn.execute(
            text(
                """
                CREATE TABLE IF NOT EXISTS shop_snapshots_global (
                  id SERIAL PRIMARY KEY,
                  shop_url TEXT NOT NULL,
                  snapshot_date DATE DEFAULT CURRENT_DATE,
                  activity_score NUMERIC,
                  trending_score NUMERIC,
                  review_growth NUMERIC,
                  products_count INT,
                  total_reviews INT,
                  created_at TIMESTAMPTZ DEFAULT now()
                );
                """
            )
        )


def upsert_shop(session, shop_data: dict) -> ShopGlobal:
    shop_url = shop_data["shop_url"]
    marketplace = shop_data["marketplace"]
    shop = (
        session.query(ShopGlobal)
        .filter(ShopGlobal.shop_url == shop_url)
        .first()
    )
    if not shop:
        shop = ShopGlobal(
            marketplace=marketplace,
            shop_name=shop_data.get("shop_name") or shop_url,
            shop_url=shop_url,
            score_global=shop_data.get("activity_score") or 0,
            revenue_est_min=shop_data.get("revenue_est_min"),
            revenue_est_max=shop_data.get("revenue_est_max"),
            winners_count=shop_data.get("winners_count") or 0,
            last_scraped_at=datetime.now(),
        )
        session.add(shop)
    else:
        shop.shop_name = shop_data.get("shop_name") or shop.shop_name
        shop.score_global = shop_data.get("activity_score") or shop.score_global
        shop.revenue_est_min = shop_data.get("revenue_est_min") or shop.revenue_est_min
        shop.revenue_est_max = shop_data.get("revenue_est_max") or shop.revenue_est_max
        shop.winners_count = shop_data.get("winners_count") or shop.winners_count
        shop.last_scraped_at = datetime.now()
    return shop


def upsert_product(session, product_data: dict, shop_name: str) -> ProductGlobal:
    product_url = product_data["product_url"]
    marketplace = product_data["marketplace"]
    product = (
        session.query(ProductGlobal)
        .filter(ProductGlobal.product_url == product_url)
        .first()
    )
    if not product:
        product = ProductGlobal(
            marketplace=marketplace,
            product_name=product_data.get("name") or "Produit",
            shop_name=shop_name,
            product_url=product_url,
            product_image=product_data.get("cover_image_url"),
            product_description=product_data.get("description"),
            price=product_data.get("price"),
            sales_est_min=product_data.get("sales_est_min"),
            sales_est_max=product_data.get("sales_est_max"),
            revenue_est_min=product_data.get("revenue_est_min"),
            revenue_est_max=product_data.get("revenue_est_max"),
            score_winner=product_data.get("winner_score") or 0,
            category=product_data.get("category"),
            last_scraped_at=datetime.now(),
        )
        session.add(product)
    else:
        product.product_name = product_data.get("name") or product.product_name
        product.shop_name = shop_name or product.shop_name
        product.product_image = product_data.get("cover_image_url") or product.product_image
        product.product_description = product_data.get("description") or product.product_description
        product.price = product_data.get("price") or product.price
        product.sales_est_min = product_data.get("sales_est_min") or product.sales_est_min
        product.sales_est_max = product_data.get("sales_est_max") or product.sales_est_max
        product.revenue_est_min = product_data.get("revenue_est_min") or product.revenue_est_min
        product.revenue_est_max = product_data.get("revenue_est_max") or product.revenue_est_max
        product.score_winner = product_data.get("winner_score") or product.score_winner
        product.category = product_data.get("category") or product.category
        product.last_scraped_at = datetime.now()
    return product


def insert_product_snapshot(session, product_data: dict):
    session.execute(
        text(
            """
            INSERT INTO product_snapshots_global
            (product_url, snapshot_date, winner_score, growth_index, popularity_index,
             competition_index, potential_index, review_growth, price, ranking_position,
             number_of_reviews)
            VALUES
            (:product_url, :snapshot_date, :winner_score, :growth_index, :popularity_index,
             :competition_index, :potential_index, :review_growth, :price, :ranking_position,
             :number_of_reviews)
            """
        ),
        {
            "product_url": product_data["product_url"],
            "snapshot_date": date.today(),
            "winner_score": product_data.get("winner_score"),
            "growth_index": product_data.get("growth_index"),
            "popularity_index": product_data.get("popularity_index"),
            "competition_index": product_data.get("competition_index"),
            "potential_index": product_data.get("potential_index"),
            "review_growth": product_data.get("review_growth"),
            "price": product_data.get("price"),
            "ranking_position": product_data.get("ranking_position"),
            "number_of_reviews": product_data.get("number_of_reviews"),
        },
    )


def insert_shop_snapshot(session, shop_data: dict):
    session.execute(
        text(
            """
            INSERT INTO shop_snapshots_global
            (shop_url, snapshot_date, activity_score, trending_score, review_growth,
             products_count, total_reviews)
            VALUES
            (:shop_url, :snapshot_date, :activity_score, :trending_score, :review_growth,
             :products_count, :total_reviews)
            """
        ),
        {
            "shop_url": shop_data["shop_url"],
            "snapshot_date": date.today(),
            "activity_score": shop_data.get("activity_score"),
            "trending_score": shop_data.get("trending_score"),
            "review_growth": shop_data.get("review_growth"),
            "products_count": shop_data.get("products_count"),
            "total_reviews": shop_data.get("total_reviews"),
        },
    )


def save_shop_with_products(session, shop_data: dict, products_data: list):
    """
    Sauvegarde une boutique et tous ses produits
    Utilise upsert pour éviter les doublons
    """
    # Sauvegarder la boutique
    shop = upsert_shop(session, shop_data)
    shop_name = shop.shop_name
    
    # Sauvegarder chaque produit
    saved_count = 0
    for product_data in products_data:
        try:
            # Adapter le format pour upsert_product
            product_dict = {
                "product_url": product_data.get("product_url", ""),
                "marketplace": product_data.get("marketplace", shop_data.get("marketplace", "")),
                "name": product_data.get("product_name", ""),
                "cover_image_url": product_data.get("product_image"),
                "description": product_data.get("product_description", ""),
                "price": product_data.get("price", 0),
                "category": product_data.get("category"),
                "winner_score": product_data.get("score_winner", 0)
            }
            
            # Vérifier que le produit a au moins un nom et une URL
            if product_dict["name"] and product_dict["product_url"]:
                upsert_product(session, product_dict, shop_name)
                saved_count += 1
        except Exception as e:
            print(f"      ⚠️  Erreur sauvegarde produit: {e}")
            continue
    
    return saved_count



import os
from datetime import datetime, date
from typing import Optional

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

# Import des modèles backend (ProductGlobal / ShopGlobal)
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
BACKEND_PATH = PROJECT_ROOT / "backend"
if str(BACKEND_PATH) not in sys.path:
    sys.path.insert(0, str(BACKEND_PATH))

from app.models import ProductGlobal, ShopGlobal  # type: ignore


DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://marketpulse:marketpulse_password@localhost:5433/marketpulse",
)

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(bind=engine)


def ensure_snapshot_tables():
    """Crée des tables de snapshots si elles n'existent pas (compatibilité sans migration)."""
    with engine.begin() as conn:
        conn.execute(
            text(
                """
                CREATE TABLE IF NOT EXISTS product_snapshots_global (
                  id SERIAL PRIMARY KEY,
                  product_url TEXT NOT NULL,
                  snapshot_date DATE DEFAULT CURRENT_DATE,
                  winner_score NUMERIC,
                  growth_index NUMERIC,
                  popularity_index NUMERIC,
                  competition_index NUMERIC,
                  potential_index NUMERIC,
                  review_growth NUMERIC,
                  price NUMERIC,
                  ranking_position INT,
                  number_of_reviews INT,
                  created_at TIMESTAMPTZ DEFAULT now()
                );
                """
            )
        )
        conn.execute(
            text(
                """
                CREATE TABLE IF NOT EXISTS shop_snapshots_global (
                  id SERIAL PRIMARY KEY,
                  shop_url TEXT NOT NULL,
                  snapshot_date DATE DEFAULT CURRENT_DATE,
                  activity_score NUMERIC,
                  trending_score NUMERIC,
                  review_growth NUMERIC,
                  products_count INT,
                  total_reviews INT,
                  created_at TIMESTAMPTZ DEFAULT now()
                );
                """
            )
        )


def upsert_shop(session, shop_data: dict) -> ShopGlobal:
    shop_url = shop_data["shop_url"]
    marketplace = shop_data["marketplace"]
    shop = (
        session.query(ShopGlobal)
        .filter(ShopGlobal.shop_url == shop_url)
        .first()
    )
    if not shop:
        shop = ShopGlobal(
            marketplace=marketplace,
            shop_name=shop_data.get("shop_name") or shop_url,
            shop_url=shop_url,
            score_global=shop_data.get("activity_score") or 0,
            revenue_est_min=shop_data.get("revenue_est_min"),
            revenue_est_max=shop_data.get("revenue_est_max"),
            winners_count=shop_data.get("winners_count") or 0,
            last_scraped_at=datetime.now(),
        )
        session.add(shop)
    else:
        shop.shop_name = shop_data.get("shop_name") or shop.shop_name
        shop.score_global = shop_data.get("activity_score") or shop.score_global
        shop.revenue_est_min = shop_data.get("revenue_est_min") or shop.revenue_est_min
        shop.revenue_est_max = shop_data.get("revenue_est_max") or shop.revenue_est_max
        shop.winners_count = shop_data.get("winners_count") or shop.winners_count
        shop.last_scraped_at = datetime.now()
    return shop


def upsert_product(session, product_data: dict, shop_name: str) -> ProductGlobal:
    product_url = product_data["product_url"]
    marketplace = product_data["marketplace"]
    product = (
        session.query(ProductGlobal)
        .filter(ProductGlobal.product_url == product_url)
        .first()
    )
    if not product:
        product = ProductGlobal(
            marketplace=marketplace,
            product_name=product_data.get("name") or "Produit",
            shop_name=shop_name,
            product_url=product_url,
            product_image=product_data.get("cover_image_url"),
            product_description=product_data.get("description"),
            price=product_data.get("price"),
            sales_est_min=product_data.get("sales_est_min"),
            sales_est_max=product_data.get("sales_est_max"),
            revenue_est_min=product_data.get("revenue_est_min"),
            revenue_est_max=product_data.get("revenue_est_max"),
            score_winner=product_data.get("winner_score") or 0,
            category=product_data.get("category"),
            last_scraped_at=datetime.now(),
        )
        session.add(product)
    else:
        product.product_name = product_data.get("name") or product.product_name
        product.shop_name = shop_name or product.shop_name
        product.product_image = product_data.get("cover_image_url") or product.product_image
        product.product_description = product_data.get("description") or product.product_description
        product.price = product_data.get("price") or product.price
        product.sales_est_min = product_data.get("sales_est_min") or product.sales_est_min
        product.sales_est_max = product_data.get("sales_est_max") or product.sales_est_max
        product.revenue_est_min = product_data.get("revenue_est_min") or product.revenue_est_min
        product.revenue_est_max = product_data.get("revenue_est_max") or product.revenue_est_max
        product.score_winner = product_data.get("winner_score") or product.score_winner
        product.category = product_data.get("category") or product.category
        product.last_scraped_at = datetime.now()
    return product


def insert_product_snapshot(session, product_data: dict):
    session.execute(
        text(
            """
            INSERT INTO product_snapshots_global
            (product_url, snapshot_date, winner_score, growth_index, popularity_index,
             competition_index, potential_index, review_growth, price, ranking_position,
             number_of_reviews)
            VALUES
            (:product_url, :snapshot_date, :winner_score, :growth_index, :popularity_index,
             :competition_index, :potential_index, :review_growth, :price, :ranking_position,
             :number_of_reviews)
            """
        ),
        {
            "product_url": product_data["product_url"],
            "snapshot_date": date.today(),
            "winner_score": product_data.get("winner_score"),
            "growth_index": product_data.get("growth_index"),
            "popularity_index": product_data.get("popularity_index"),
            "competition_index": product_data.get("competition_index"),
            "potential_index": product_data.get("potential_index"),
            "review_growth": product_data.get("review_growth"),
            "price": product_data.get("price"),
            "ranking_position": product_data.get("ranking_position"),
            "number_of_reviews": product_data.get("number_of_reviews"),
        },
    )


def insert_shop_snapshot(session, shop_data: dict):
    session.execute(
        text(
            """
            INSERT INTO shop_snapshots_global
            (shop_url, snapshot_date, activity_score, trending_score, review_growth,
             products_count, total_reviews)
            VALUES
            (:shop_url, :snapshot_date, :activity_score, :trending_score, :review_growth,
             :products_count, :total_reviews)
            """
        ),
        {
            "shop_url": shop_data["shop_url"],
            "snapshot_date": date.today(),
            "activity_score": shop_data.get("activity_score"),
            "trending_score": shop_data.get("trending_score"),
            "review_growth": shop_data.get("review_growth"),
            "products_count": shop_data.get("products_count"),
            "total_reviews": shop_data.get("total_reviews"),
        },
    )


def save_shop_with_products(session, shop_data: dict, products_data: list):
    """
    Sauvegarde une boutique et tous ses produits
    Utilise upsert pour éviter les doublons
    """
    # Sauvegarder la boutique
    shop = upsert_shop(session, shop_data)
    shop_name = shop.shop_name
    
    # Sauvegarder chaque produit
    saved_count = 0
    for product_data in products_data:
        try:
            # Adapter le format pour upsert_product
            product_dict = {
                "product_url": product_data.get("product_url", ""),
                "marketplace": product_data.get("marketplace", shop_data.get("marketplace", "")),
                "name": product_data.get("product_name", ""),
                "cover_image_url": product_data.get("product_image"),
                "description": product_data.get("product_description", ""),
                "price": product_data.get("price", 0),
                "category": product_data.get("category"),
                "winner_score": product_data.get("score_winner", 0)
            }
            
            # Vérifier que le produit a au moins un nom et une URL
            if product_dict["name"] and product_dict["product_url"]:
                upsert_product(session, product_dict, shop_name)
                saved_count += 1
        except Exception as e:
            print(f"      ⚠️  Erreur sauvegarde produit: {e}")
            continue
    
    return saved_count

