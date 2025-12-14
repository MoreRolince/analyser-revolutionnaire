"""
Déduplication basique des produits digitaux détectés.
"""
import hashlib
from typing import List, Dict, Any


class ProductDeduplicator:
    """Outils simples de déduplication et de fusion de produits digitaux."""

    @staticmethod
    def _hash_product(product: Dict[str, Any]) -> str:
        url = (product.get("landing_page_url") or "").strip().lower()
        title = (product.get("product_title") or "").strip().lower()
        key = f"{url}|{title}"
        return hashlib.sha256(key.encode("utf-8")).hexdigest()

    @classmethod
    def find_duplicates(cls, products: List[Dict[str, Any]]) -> Dict[str, List[Dict[str, Any]]]:
        """Trouve les produits dupliqués basés sur un hash URL+title."""
        groups: Dict[str, List[Dict[str, Any]]] = {}
        for product in products:
            h = cls._hash_product(product)
            groups.setdefault(h, []).append(product)
        # Ne garder que les groupes avec >1 élément
        return {h: items for h, items in groups.items() if len(items) > 1}

    @staticmethod
    def merge_products(products: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Fusionne une liste de produits en privilégiant les valeurs non vides."""
        merged: Dict[str, Any] = {}
        fields = [
            "product_title",
            "landing_page_url",
            "price",
            "seller_name",
            "description",
            "images",
            "bullet_points",
            "cta_text",
            "social_proof",
            "page_structure",
            "marketplace",
        ]
        for field in fields:
            for product in products:
                val = product.get(field)
                if val not in (None, "", [], {}):
                    merged[field] = val
                    break
        # Conserver l'historique simple
        merged["history"] = products
        return merged

    @classmethod
    def detect_price_changes(cls, products: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Détecte les changements de prix basiques (comparaison pair-à-pair dans un groupe).
        Retourne une liste de dicts {product_title, previous_price, current_price}.
        """
        changes: List[Dict[str, Any]] = []
        groups = cls.find_duplicates(products)
        for _, items in groups.items():
            prices = [p.get("price") for p in items if p.get("price") is not None]
            if len(prices) >= 2:
                prev = prices[0]
                curr = prices[-1]
                if prev != curr:
                    changes.append({
                        "product_title": items[-1].get("product_title", ""),
                        "previous_price": prev,
                        "current_price": curr,
                    })
        return changes

