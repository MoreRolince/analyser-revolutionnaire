"""
Scoring simplifié des produits digitaux détectés.
"""
from typing import Dict, Any
from datetime import datetime


class WinnerScorer:
    """Calcule un score winner heuristique (0-100)."""

    @staticmethod
    def calculate_winner_score(product: Dict[str, Any], ads: Dict[str, Any], landing_page: Dict[str, Any]) -> Dict[str, Any]:
        ads_count = len(ads)
        countries_targeted = len({ad.get("country_targeting") for ad in ads if ad.get("country_targeting")})
        ad_longevity_days = 30  # placeholder
        advertiser_pages_count = len({ad.get("advertiser_page") for ad in ads if ad.get("advertiser_page")})

        price = product.get("price") or 0
        price_attractiveness = 15 if 5000 <= price <= 30000 else 8 if price > 0 else 0
        offer_clarity = 10 if product.get("product_title") else 0
        has_bonuses = 5 if "bonus" in (product.get("description") or "").lower() else 0
        cta_strength = 5 if landing_page.get("cta_text") else 0
        positioning_niche = 5

        marketplace = (product.get("marketplace") or "").lower()
        marketplace_bonus = 15 if marketplace in ("maketou", "chariow") else 10 if "systeme.io" in marketplace else 0

        ad_score = min(40, ads_count * 4) + min(10, countries_targeted * 2) + min(10, advertiser_pages_count * 2)
        landing_score = price_attractiveness + offer_clarity + has_bonuses + cta_strength + positioning_niche
        winner_score = min(100, ad_score + landing_score + marketplace_bonus)

        return {
            "winner_score": winner_score,
            "ads_count": ads_count,
            "countries_targeted": countries_targeted,
            "ad_longevity_days": ad_longevity_days,
            "advertiser_pages_count": advertiser_pages_count,
            "price_attractiveness": price_attractiveness,
            "offer_clarity": offer_clarity,
            "has_bonuses": bool(has_bonuses),
            "cta_strength": cta_strength,
            "positioning_niche": positioning_niche,
            "marketplace_bonus": marketplace_bonus,
            "scoring_details": {
                "calculated_at": datetime.now().isoformat(),
            },
        }

