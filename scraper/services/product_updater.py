"""
Système de mise à jour des produits avec détection de changements
Détecte: nouveaux produits, changement de prix, description, images, avis
"""
from typing import Dict, Any, List, Optional
from datetime import datetime
import hashlib


class ProductUpdater:
    """Gère la mise à jour des produits et détecte les changements"""
    
    def __init__(self):
        pass
    
    def detect_changes(self, existing_product: Dict[str, Any], new_product: Dict[str, Any]) -> Dict[str, Any]:
        """
        Compare un produit existant avec une nouvelle version
        Retourne un dictionnaire des changements détectés
        """
        changes = {
            "has_changes": False,
            "new_product": False,
            "price_changed": False,
            "price_old": None,
            "price_new": None,
            "description_changed": False,
            "images_changed": False,
            "images_added": [],
            "reviews_increased": False,
            "reviews_old": None,
            "reviews_new": None,
            "rating_changed": False,
            "rating_old": None,
            "rating_new": None,
            "category_changed": False,
            "category_old": None,
            "category_new": None
        }
        
        # Si le produit n'existe pas, c'est un nouveau produit
        if not existing_product:
            changes["new_product"] = True
            changes["has_changes"] = True
            return changes
        
        # Vérifier le prix
        old_price = existing_product.get("price", 0)
        new_price = new_product.get("price", 0)
        if old_price != new_price and old_price > 0 and new_price > 0:
            changes["price_changed"] = True
            changes["price_old"] = old_price
            changes["price_new"] = new_price
            changes["has_changes"] = True
        
        # Vérifier la description
        old_desc = existing_product.get("description", "")
        new_desc = new_product.get("description", "")
        if old_desc != new_desc and old_desc and new_desc:
            # Calculer un hash pour détecter les changements significatifs
            old_hash = hashlib.md5(old_desc.encode()).hexdigest()
            new_hash = hashlib.md5(new_desc.encode()).hexdigest()
            if old_hash != new_hash:
                changes["description_changed"] = True
                changes["has_changes"] = True
        
        # Vérifier les images
        old_images = set(existing_product.get("images", []))
        new_images = set(new_product.get("images", []))
        if old_images != new_images:
            changes["images_changed"] = True
            changes["images_added"] = list(new_images - old_images)
            changes["has_changes"] = True
        
        # Vérifier les avis
        old_reviews = existing_product.get("reviews_count")
        new_reviews = new_product.get("reviews_count")
        if old_reviews is not None and new_reviews is not None:
            if new_reviews > old_reviews:
                changes["reviews_increased"] = True
                changes["reviews_old"] = old_reviews
                changes["reviews_new"] = new_reviews
                changes["has_changes"] = True
        
        # Vérifier le rating
        old_rating = existing_product.get("rating")
        new_rating = new_product.get("rating")
        if old_rating is not None and new_rating is not None:
            if abs(old_rating - new_rating) > 0.1:  # Changement significatif
                changes["rating_changed"] = True
                changes["rating_old"] = old_rating
                changes["rating_new"] = new_rating
                changes["has_changes"] = True
        
        # Vérifier la catégorie
        old_category = existing_product.get("category")
        new_category = new_product.get("category")
        if old_category != new_category:
            changes["category_changed"] = True
            changes["category_old"] = old_category
            changes["category_new"] = new_category
            changes["has_changes"] = True
        
        return changes
    
    def update_product(self, existing_product: Dict[str, Any], new_product: Dict[str, Any], changes: Dict[str, Any]) -> Dict[str, Any]:
        """
        Met à jour un produit existant avec les nouvelles données
        Conserve l'historique des changements
        """
        updated_product = existing_product.copy() if existing_product else {}
        
        # Mettre à jour toutes les données
        updated_product.update({
            "id": new_product.get("id"),
            "url": new_product.get("url"),
            "title": new_product.get("title"),
            "price": new_product.get("price", 0),
            "description": new_product.get("description", ""),
            "images": new_product.get("images", []),
            "category": new_product.get("category"),
            "rating": new_product.get("rating"),
            "reviews_count": new_product.get("reviews_count"),
            "date_added": new_product.get("date_added"),
            "shop_name": new_product.get("shop_name"),
            "shop_url": new_product.get("shop_url"),
            "marketplace": new_product.get("marketplace"),
            "scraped_at": new_product.get("scraped_at", datetime.now().isoformat()),
            "updated_at": datetime.now().isoformat()
        })
        
        # Ajouter l'historique des changements
        if "change_history" not in updated_product:
            updated_product["change_history"] = []
        
        if changes["has_changes"]:
            updated_product["change_history"].append({
                "timestamp": datetime.now().isoformat(),
                "changes": changes
            })
        
        return updated_product
    
    def find_new_products(self, existing_products: List[Dict[str, Any]], new_products: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Trouve les nouveaux produits (ceux qui n'existent pas encore)
        """
        existing_urls = {p.get("url") for p in existing_products if p.get("url")}
        new_products_list = [p for p in new_products if p.get("url") not in existing_urls]
        return new_products_list
    
    def calculate_growth_score(self, product: Dict[str, Any], changes: Dict[str, Any]) -> float:
        """
        Calcule un score de croissance basé sur les changements
        Utilisé pour identifier les "winners"
        """
        score = 0.0
        
        # Nouveau produit = bonus
        if changes.get("new_product"):
            score += 20.0
        
        # Augmentation des avis = bon signe
        if changes.get("reviews_increased"):
            reviews_increase = changes.get("reviews_new", 0) - changes.get("reviews_old", 0)
            score += min(reviews_increase * 2, 30.0)  # Max 30 points
        
        # Amélioration du rating
        if changes.get("rating_changed") and changes.get("rating_new", 0) > changes.get("rating_old", 0):
            rating_increase = changes.get("rating_new", 0) - changes.get("rating_old", 0)
            score += rating_increase * 10  # 1 point de rating = 10 points
        
        # Nouvelles images = produit mis à jour
        if changes.get("images_changed") and changes.get("images_added"):
            score += len(changes.get("images_added", [])) * 2
        
        # Description mise à jour = produit actif
        if changes.get("description_changed"):
            score += 5.0
        
        return score


Système de mise à jour des produits avec détection de changements
Détecte: nouveaux produits, changement de prix, description, images, avis
"""
from typing import Dict, Any, List, Optional
from datetime import datetime
import hashlib


class ProductUpdater:
    """Gère la mise à jour des produits et détecte les changements"""
    
    def __init__(self):
        pass
    
    def detect_changes(self, existing_product: Dict[str, Any], new_product: Dict[str, Any]) -> Dict[str, Any]:
        """
        Compare un produit existant avec une nouvelle version
        Retourne un dictionnaire des changements détectés
        """
        changes = {
            "has_changes": False,
            "new_product": False,
            "price_changed": False,
            "price_old": None,
            "price_new": None,
            "description_changed": False,
            "images_changed": False,
            "images_added": [],
            "reviews_increased": False,
            "reviews_old": None,
            "reviews_new": None,
            "rating_changed": False,
            "rating_old": None,
            "rating_new": None,
            "category_changed": False,
            "category_old": None,
            "category_new": None
        }
        
        # Si le produit n'existe pas, c'est un nouveau produit
        if not existing_product:
            changes["new_product"] = True
            changes["has_changes"] = True
            return changes
        
        # Vérifier le prix
        old_price = existing_product.get("price", 0)
        new_price = new_product.get("price", 0)
        if old_price != new_price and old_price > 0 and new_price > 0:
            changes["price_changed"] = True
            changes["price_old"] = old_price
            changes["price_new"] = new_price
            changes["has_changes"] = True
        
        # Vérifier la description
        old_desc = existing_product.get("description", "")
        new_desc = new_product.get("description", "")
        if old_desc != new_desc and old_desc and new_desc:
            # Calculer un hash pour détecter les changements significatifs
            old_hash = hashlib.md5(old_desc.encode()).hexdigest()
            new_hash = hashlib.md5(new_desc.encode()).hexdigest()
            if old_hash != new_hash:
                changes["description_changed"] = True
                changes["has_changes"] = True
        
        # Vérifier les images
        old_images = set(existing_product.get("images", []))
        new_images = set(new_product.get("images", []))
        if old_images != new_images:
            changes["images_changed"] = True
            changes["images_added"] = list(new_images - old_images)
            changes["has_changes"] = True
        
        # Vérifier les avis
        old_reviews = existing_product.get("reviews_count")
        new_reviews = new_product.get("reviews_count")
        if old_reviews is not None and new_reviews is not None:
            if new_reviews > old_reviews:
                changes["reviews_increased"] = True
                changes["reviews_old"] = old_reviews
                changes["reviews_new"] = new_reviews
                changes["has_changes"] = True
        
        # Vérifier le rating
        old_rating = existing_product.get("rating")
        new_rating = new_product.get("rating")
        if old_rating is not None and new_rating is not None:
            if abs(old_rating - new_rating) > 0.1:  # Changement significatif
                changes["rating_changed"] = True
                changes["rating_old"] = old_rating
                changes["rating_new"] = new_rating
                changes["has_changes"] = True
        
        # Vérifier la catégorie
        old_category = existing_product.get("category")
        new_category = new_product.get("category")
        if old_category != new_category:
            changes["category_changed"] = True
            changes["category_old"] = old_category
            changes["category_new"] = new_category
            changes["has_changes"] = True
        
        return changes
    
    def update_product(self, existing_product: Dict[str, Any], new_product: Dict[str, Any], changes: Dict[str, Any]) -> Dict[str, Any]:
        """
        Met à jour un produit existant avec les nouvelles données
        Conserve l'historique des changements
        """
        updated_product = existing_product.copy() if existing_product else {}
        
        # Mettre à jour toutes les données
        updated_product.update({
            "id": new_product.get("id"),
            "url": new_product.get("url"),
            "title": new_product.get("title"),
            "price": new_product.get("price", 0),
            "description": new_product.get("description", ""),
            "images": new_product.get("images", []),
            "category": new_product.get("category"),
            "rating": new_product.get("rating"),
            "reviews_count": new_product.get("reviews_count"),
            "date_added": new_product.get("date_added"),
            "shop_name": new_product.get("shop_name"),
            "shop_url": new_product.get("shop_url"),
            "marketplace": new_product.get("marketplace"),
            "scraped_at": new_product.get("scraped_at", datetime.now().isoformat()),
            "updated_at": datetime.now().isoformat()
        })
        
        # Ajouter l'historique des changements
        if "change_history" not in updated_product:
            updated_product["change_history"] = []
        
        if changes["has_changes"]:
            updated_product["change_history"].append({
                "timestamp": datetime.now().isoformat(),
                "changes": changes
            })
        
        return updated_product
    
    def find_new_products(self, existing_products: List[Dict[str, Any]], new_products: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Trouve les nouveaux produits (ceux qui n'existent pas encore)
        """
        existing_urls = {p.get("url") for p in existing_products if p.get("url")}
        new_products_list = [p for p in new_products if p.get("url") not in existing_urls]
        return new_products_list
    
    def calculate_growth_score(self, product: Dict[str, Any], changes: Dict[str, Any]) -> float:
        """
        Calcule un score de croissance basé sur les changements
        Utilisé pour identifier les "winners"
        """
        score = 0.0
        
        # Nouveau produit = bonus
        if changes.get("new_product"):
            score += 20.0
        
        # Augmentation des avis = bon signe
        if changes.get("reviews_increased"):
            reviews_increase = changes.get("reviews_new", 0) - changes.get("reviews_old", 0)
            score += min(reviews_increase * 2, 30.0)  # Max 30 points
        
        # Amélioration du rating
        if changes.get("rating_changed") and changes.get("rating_new", 0) > changes.get("rating_old", 0):
            rating_increase = changes.get("rating_new", 0) - changes.get("rating_old", 0)
            score += rating_increase * 10  # 1 point de rating = 10 points
        
        # Nouvelles images = produit mis à jour
        if changes.get("images_changed") and changes.get("images_added"):
            score += len(changes.get("images_added", [])) * 2
        
        # Description mise à jour = produit actif
        if changes.get("description_changed"):
            score += 5.0
        
        return score

