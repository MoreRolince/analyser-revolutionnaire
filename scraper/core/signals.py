"""Calcul des signaux produits/shops."""
from __future__ import annotations


def compute_product_signals(product: dict, previous: dict | None) -> dict:
    prev_reviews = (previous or {}).get("number_of_reviews") or 0
    curr_reviews = product.get("number_of_reviews") or 0
    review_growth = max(curr_reviews - prev_reviews, 0)

    popularity_index = min(curr_reviews, 500) / 500  # 0-1
    competition_index = 1 - min((product.get("ranking_position") or 500) / 500, 1)
    potential_index = 1.0 if product.get("description") and product.get("cover_image_url") else 0.6

    return {
        "review_growth": review_growth,
        "growth_index": review_growth,
        "popularity_index": popularity_index,
        "competition_index": competition_index,
        "potential_index": potential_index,
    }


def compute_shop_signals(shop: dict, previous: dict | None) -> dict:
    prev_reviews = (previous or {}).get("total_reviews") or 0
    curr_reviews = shop.get("total_reviews") or 0
    review_growth = max(curr_reviews - prev_reviews, 0)

    activity_score = (shop.get("products_count") or 0) / 50
    trending_score = review_growth / 20

    return {
        "review_growth": review_growth,
        "activity_score": activity_score,
        "trending_score": trending_score,
    }



from __future__ import annotations


def compute_product_signals(product: dict, previous: dict | None) -> dict:
    prev_reviews = (previous or {}).get("number_of_reviews") or 0
    curr_reviews = product.get("number_of_reviews") or 0
    review_growth = max(curr_reviews - prev_reviews, 0)

    popularity_index = min(curr_reviews, 500) / 500  # 0-1
    competition_index = 1 - min((product.get("ranking_position") or 500) / 500, 1)
    potential_index = 1.0 if product.get("description") and product.get("cover_image_url") else 0.6

    return {
        "review_growth": review_growth,
        "growth_index": review_growth,
        "popularity_index": popularity_index,
        "competition_index": competition_index,
        "potential_index": potential_index,
    }


def compute_shop_signals(shop: dict, previous: dict | None) -> dict:
    prev_reviews = (previous or {}).get("total_reviews") or 0
    curr_reviews = shop.get("total_reviews") or 0
    review_growth = max(curr_reviews - prev_reviews, 0)

    activity_score = (shop.get("products_count") or 0) / 50
    trending_score = review_growth / 20

    return {
        "review_growth": review_growth,
        "activity_score": activity_score,
        "trending_score": trending_score,
    }


