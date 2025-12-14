from typing import Dict, Any

def calculate_shop_score(data: Dict[str, Any]) -> float:
    """
    Calcule un score de 0-100 pour une boutique
    """
    score = 0.0
    
    # Score basé sur le nombre de produits (max 30 points)
    product_count = data.get("product_count", 0)
    if product_count > 50:
        score += 30
    elif product_count > 30:
        score += 25
    elif product_count > 20:
        score += 20
    elif product_count > 10:
        score += 15
    elif product_count > 5:
        score += 10
    else:
        score += 5
    
    # Score basé sur les ventes estimées (max 30 points)
    estimated_sales = data.get("estimated_sales", 0)
    if estimated_sales > 200:
        score += 30
    elif estimated_sales > 100:
        score += 25
    elif estimated_sales > 50:
        score += 20
    elif estimated_sales > 20:
        score += 15
    else:
        score += 10
    
    # Score basé sur les points forts/faibles (max 20 points)
    strengths = data.get("strengths", [])
    weaknesses = data.get("weaknesses", [])
    strength_score = min(len(strengths) * 5, 15)
    weakness_penalty = min(len(weaknesses) * 2, 10)
    score += strength_score - weakness_penalty
    
    # Score basé sur la croissance (max 20 points)
    growth_rate = data.get("growth_rate", 0)
    if growth_rate > 20:
        score += 20
    elif growth_rate > 10:
        score += 15
    elif growth_rate > 5:
        score += 10
    else:
        score += 5
    
    return min(score, 100.0)

def calculate_product_score(data: Dict[str, Any]) -> float:
    """
    Calcule un score de 0-100 pour un produit
    """
    score = 0.0
    
    # Score basé sur les ventes quotidiennes estimées (max 40 points)
    daily_sales = data.get("estimated_daily_sales", 0)
    if daily_sales > 20:
        score += 40
    elif daily_sales > 10:
        score += 30
    elif daily_sales > 5:
        score += 20
    else:
        score += 10
    
    # Score basé sur la tendance (max 30 points)
    trend = data.get("trend", "stable")
    if trend == "rising":
        score += 30
    elif trend == "stable":
        score += 20
    else:
        score += 10
    
    # Score basé sur le niveau de concurrence (max 20 points)
    competition = data.get("competition_level", "Moyen")
    if competition == "Faible":
        score += 20
    elif competition == "Moyen":
        score += 15
    else:
        score += 10
    
    # Pénalité pour les risques (max -10 points)
    risks = data.get("risks", [])
    score -= min(len(risks) * 2, 10)
    
    # Score basé sur le prix (max 10 points)
    ideal_price = data.get("ideal_price")
    if ideal_price:
        score += 10
    
    return min(max(score, 0.0), 100.0)

