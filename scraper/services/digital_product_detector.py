"""
Détecteur de produits digitaux pour le marché africain
"""
import re
from typing import Dict, Any, List


class DigitalProductDetector:
    """Détecte si un produit est un produit digital"""
    
    # Mots-clés produits digitaux
    DIGITAL_KEYWORDS = [
        'ebook', 'e-book', 'livre numérique', 'livre digital',
        'template', 'modèle', 'modèle prêt à l\'emploi',
        'formation', 'cours', 'tutoriel', 'guide',
        'logiciel', 'software', 'application', 'app',
        'plugin', 'extension', 'addon',
        'theme', 'thème', 'template wordpress',
        'pdf', 'guide pdf', 'manuel pdf',
        'affiliation', 'programme d\'affiliation',
        'dropshipping', 'business digital',
        'canva', 'figma', 'notion', 'clickfunnels',
        'funnel', 'landing page', 'page de vente',
        'copywriting', 'marketing digital',
        'coaching', 'mentorat', 'consultation',
        'graphisme', 'design', 'logo', 'bannière',
        'video', 'vidéo', 'formation vidéo',
        'audio', 'podcast', 'formation audio',
    ]
    
    # Mots-clés africains pour cibler le marché
    AFRICAN_KEYWORDS = [
        'afrique', 'africain', 'afrique francophone',
        'cameroun', 'sénégal', 'côte d\'ivoire', 'mali',
        'burkina faso', 'bénin', 'togo', 'gabon',
        'congo', 'rdc', 'madagascar', 'tunisie',
        'maroc', 'algérie', 'fcfa', 'xof', 'xaf',
        'franc cfa', 'cfa', 'west africa', 'afrique de l\'ouest',
        'afrique centrale', 'afrique du nord',
    ]
    
    # Catégories de produits digitaux
    DIGITAL_CATEGORIES = [
        'ebook', 'formation', 'template', 'logiciel',
        'plugin', 'theme', 'application', 'software',
        'cours', 'tutoriel', 'guide', 'coaching',
        'consultation', 'graphisme', 'design',
        'marketing', 'affiliation', 'dropshipping',
    ]
    
    @classmethod
    def is_digital_product(cls, product: Dict[str, Any]) -> bool:
        """
        Vérifie si un produit est un produit digital
        """
        title = (product.get('title', '') or '').lower()
        description = (product.get('description', '') or '').lower()
        category = (product.get('category', '') or '').lower()
        
        # Vérifier dans le titre
        title_text = f"{title} {description} {category}"
        
        # Vérifier si au moins un mot-clé digital est présent
        has_digital_keyword = any(keyword in title_text for keyword in cls.DIGITAL_KEYWORDS)
        
        # Vérifier la catégorie
        has_digital_category = any(cat in category for cat in cls.DIGITAL_CATEGORIES)
        
        return has_digital_keyword or has_digital_category
    
    @classmethod
    def is_african_market(cls, product: Dict[str, Any]) -> bool:
        """
        Vérifie si le produit cible le marché africain
        """
        title = (product.get('title', '') or '').lower()
        description = (product.get('description', '') or '').lower()
        shop_name = (product.get('shop_name', '') or '').lower()
        
        text = f"{title} {description} {shop_name}"
        
        # Vérifier si au moins un mot-clé africain est présent
        has_african_keyword = any(keyword in text for keyword in cls.AFRICAN_KEYWORDS)
        
        # Vérifier le prix en FCFA (indicateur du marché africain)
        price = product.get('price', 0)
        has_fcfa_price = price > 0 and price < 1000000  # Prix raisonnable en FCFA
        
        return has_african_keyword or has_fcfa_price
    
    @classmethod
    def calculate_winner_score(cls, product: Dict[str, Any]) -> float:
        """
        Calcule un score "winner" pour un produit digital africain
        Score de 0 à 100
        """
        score = 0.0
        
        # 1. Produit digital confirmé (20 points)
        if cls.is_digital_product(product):
            score += 20.0
        
        # 2. Marché africain confirmé (15 points)
        if cls.is_african_market(product):
            score += 15.0
        
        # 3. Prix raisonnable pour le marché africain (20 points)
        price = product.get('price', 0)
        if 5000 <= price <= 50000:  # Prix idéal pour produits digitaux africains
            score += 20.0
        elif 1000 <= price < 5000 or 50000 < price <= 100000:
            score += 15.0
        elif price > 0:
            score += 10.0
        
        # 4. Description complète (15 points)
        description = product.get('description', '')
        if len(description) > 200:
            score += 15.0
        elif len(description) > 100:
            score += 10.0
        elif len(description) > 50:
            score += 5.0
        
        # 5. Image présente (10 points)
        images = product.get('images', [])
        if images and len(images) > 0:
            score += 10.0
        
        # 6. Catégorie claire (10 points)
        category = product.get('category', '')
        if category and len(category) > 2:
            score += 10.0
        
        # 7. Titre descriptif (10 points)
        title = product.get('title', '')
        if len(title) > 20 and len(title) < 100:
            score += 10.0
        elif len(title) > 10:
            score += 5.0
        
        # Bonus: Produit avec plusieurs images (bonne présentation)
        if images and len(images) > 1:
            score += 5.0
        
        # Bonus: Description avec mots-clés digitaux
        description_lower = description.lower()
        digital_matches = sum(1 for kw in cls.DIGITAL_KEYWORDS if kw in description_lower)
        if digital_matches >= 3:
            score += 5.0
        elif digital_matches >= 2:
            score += 3.0
        
        return min(score, 100.0)
    
    @classmethod
    def is_winner(cls, product: Dict[str, Any], min_score: float = 60.0) -> bool:
        """
        Détermine si un produit est un "winner"
        Un winner doit être un produit digital avec un bon score
        """
        if not cls.is_digital_product(product):
            return False
        
        score = cls.calculate_winner_score(product)
        return score >= min_score
    
    @classmethod
    def filter_digital_products(cls, products: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Filtre uniquement les produits digitaux
        """
        return [p for p in products if cls.is_digital_product(p)]
    
    @classmethod
    def filter_winners(cls, products: List[Dict[str, Any]], min_score: float = 60.0) -> List[Dict[str, Any]]:
        """
        Filtre uniquement les "winners" (produits digitaux avec bon score)
        """
        winners = []
        for product in products:
            if cls.is_winner(product, min_score):
                # Ajouter le score au produit
                product['winner_score'] = cls.calculate_winner_score(product)
                winners.append(product)
        return winners


Détecteur de produits digitaux pour le marché africain
"""
import re
from typing import Dict, Any, List


class DigitalProductDetector:
    """Détecte si un produit est un produit digital"""
    
    # Mots-clés produits digitaux
    DIGITAL_KEYWORDS = [
        'ebook', 'e-book', 'livre numérique', 'livre digital',
        'template', 'modèle', 'modèle prêt à l\'emploi',
        'formation', 'cours', 'tutoriel', 'guide',
        'logiciel', 'software', 'application', 'app',
        'plugin', 'extension', 'addon',
        'theme', 'thème', 'template wordpress',
        'pdf', 'guide pdf', 'manuel pdf',
        'affiliation', 'programme d\'affiliation',
        'dropshipping', 'business digital',
        'canva', 'figma', 'notion', 'clickfunnels',
        'funnel', 'landing page', 'page de vente',
        'copywriting', 'marketing digital',
        'coaching', 'mentorat', 'consultation',
        'graphisme', 'design', 'logo', 'bannière',
        'video', 'vidéo', 'formation vidéo',
        'audio', 'podcast', 'formation audio',
    ]
    
    # Mots-clés africains pour cibler le marché
    AFRICAN_KEYWORDS = [
        'afrique', 'africain', 'afrique francophone',
        'cameroun', 'sénégal', 'côte d\'ivoire', 'mali',
        'burkina faso', 'bénin', 'togo', 'gabon',
        'congo', 'rdc', 'madagascar', 'tunisie',
        'maroc', 'algérie', 'fcfa', 'xof', 'xaf',
        'franc cfa', 'cfa', 'west africa', 'afrique de l\'ouest',
        'afrique centrale', 'afrique du nord',
    ]
    
    # Catégories de produits digitaux
    DIGITAL_CATEGORIES = [
        'ebook', 'formation', 'template', 'logiciel',
        'plugin', 'theme', 'application', 'software',
        'cours', 'tutoriel', 'guide', 'coaching',
        'consultation', 'graphisme', 'design',
        'marketing', 'affiliation', 'dropshipping',
    ]
    
    @classmethod
    def is_digital_product(cls, product: Dict[str, Any]) -> bool:
        """
        Vérifie si un produit est un produit digital
        """
        title = (product.get('title', '') or '').lower()
        description = (product.get('description', '') or '').lower()
        category = (product.get('category', '') or '').lower()
        
        # Vérifier dans le titre
        title_text = f"{title} {description} {category}"
        
        # Vérifier si au moins un mot-clé digital est présent
        has_digital_keyword = any(keyword in title_text for keyword in cls.DIGITAL_KEYWORDS)
        
        # Vérifier la catégorie
        has_digital_category = any(cat in category for cat in cls.DIGITAL_CATEGORIES)
        
        return has_digital_keyword or has_digital_category
    
    @classmethod
    def is_african_market(cls, product: Dict[str, Any]) -> bool:
        """
        Vérifie si le produit cible le marché africain
        """
        title = (product.get('title', '') or '').lower()
        description = (product.get('description', '') or '').lower()
        shop_name = (product.get('shop_name', '') or '').lower()
        
        text = f"{title} {description} {shop_name}"
        
        # Vérifier si au moins un mot-clé africain est présent
        has_african_keyword = any(keyword in text for keyword in cls.AFRICAN_KEYWORDS)
        
        # Vérifier le prix en FCFA (indicateur du marché africain)
        price = product.get('price', 0)
        has_fcfa_price = price > 0 and price < 1000000  # Prix raisonnable en FCFA
        
        return has_african_keyword or has_fcfa_price
    
    @classmethod
    def calculate_winner_score(cls, product: Dict[str, Any]) -> float:
        """
        Calcule un score "winner" pour un produit digital africain
        Score de 0 à 100
        """
        score = 0.0
        
        # 1. Produit digital confirmé (20 points)
        if cls.is_digital_product(product):
            score += 20.0
        
        # 2. Marché africain confirmé (15 points)
        if cls.is_african_market(product):
            score += 15.0
        
        # 3. Prix raisonnable pour le marché africain (20 points)
        price = product.get('price', 0)
        if 5000 <= price <= 50000:  # Prix idéal pour produits digitaux africains
            score += 20.0
        elif 1000 <= price < 5000 or 50000 < price <= 100000:
            score += 15.0
        elif price > 0:
            score += 10.0
        
        # 4. Description complète (15 points)
        description = product.get('description', '')
        if len(description) > 200:
            score += 15.0
        elif len(description) > 100:
            score += 10.0
        elif len(description) > 50:
            score += 5.0
        
        # 5. Image présente (10 points)
        images = product.get('images', [])
        if images and len(images) > 0:
            score += 10.0
        
        # 6. Catégorie claire (10 points)
        category = product.get('category', '')
        if category and len(category) > 2:
            score += 10.0
        
        # 7. Titre descriptif (10 points)
        title = product.get('title', '')
        if len(title) > 20 and len(title) < 100:
            score += 10.0
        elif len(title) > 10:
            score += 5.0
        
        # Bonus: Produit avec plusieurs images (bonne présentation)
        if images and len(images) > 1:
            score += 5.0
        
        # Bonus: Description avec mots-clés digitaux
        description_lower = description.lower()
        digital_matches = sum(1 for kw in cls.DIGITAL_KEYWORDS if kw in description_lower)
        if digital_matches >= 3:
            score += 5.0
        elif digital_matches >= 2:
            score += 3.0
        
        return min(score, 100.0)
    
    @classmethod
    def is_winner(cls, product: Dict[str, Any], min_score: float = 60.0) -> bool:
        """
        Détermine si un produit est un "winner"
        Un winner doit être un produit digital avec un bon score
        """
        if not cls.is_digital_product(product):
            return False
        
        score = cls.calculate_winner_score(product)
        return score >= min_score
    
    @classmethod
    def filter_digital_products(cls, products: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Filtre uniquement les produits digitaux
        """
        return [p for p in products if cls.is_digital_product(p)]
    
    @classmethod
    def filter_winners(cls, products: List[Dict[str, Any]], min_score: float = 60.0) -> List[Dict[str, Any]]:
        """
        Filtre uniquement les "winners" (produits digitaux avec bon score)
        """
        winners = []
        for product in products:
            if cls.is_winner(product, min_score):
                # Ajouter le score au produit
                product['winner_score'] = cls.calculate_winner_score(product)
                winners.append(product)
        return winners

