# 📊 Explication du Système de Scoring WINNER

## 🎯 Objectif

Le score WINNER (0-100) détermine si un produit digital est un "winner" - c'est-à-dire un produit qui performe bien sur Facebook Ads et mérite d'être identifié comme opportunité.

## 🔍 Comment le score est calculé

Le score est calculé par la classe `WinnerScorer` dans `scraper/services/winner_scorer.py`.

### 📐 Formule globale

```
winner_score = min(100, ad_score + landing_score + marketplace_bonus)
```

### 🎯 Composantes du score

#### 1. **AD_SCORE** (0-60 points)
Score basé sur les annonces Facebook Ads détectées :

- **Nombre d'annonces** (0-40 points)
  - `min(40, ads_count * 4)`
  - Exemple: 10 annonces = 40 points (max)
  - Exemple: 5 annonces = 20 points
  - Exemple: 1 annonce = 4 points

- **Pays ciblés** (0-10 points)
  - `min(10, countries_targeted * 2)`
  - Plus le produit est diffusé dans plusieurs pays, plus c'est un signal positif

- **Pages publicitaires uniques** (0-10 points)
  - `min(10, advertiser_pages_count * 2)`
  - Si plusieurs pages font la pub du même produit, c'est un bon signal

#### 2. **LANDING_SCORE** (0-35 points)
Score basé sur la qualité de la landing page :

- **Attractivité du prix** (0-15 points)
  - 15 points si prix entre 5,000 et 30,000 FCFA (sweet spot)
  - 8 points si prix > 0 (en dehors du sweet spot)
  - 0 point si pas de prix

- **Clarté de l'offre** (0-10 points)
  - 10 points si le produit a un titre (obligatoire)
  - 0 point sinon

- **Présence de bonus** (0-5 points)
  - 5 points si le mot "bonus" apparaît dans la description
  - 0 point sinon

- **Force du CTA** (0-5 points)
  - 5 points si un CTA (Call To Action) est détecté sur la landing page
  - 0 point sinon

- **Positionnement niche** (5 points fixes)
  - 5 points toujours accordés

#### 3. **MARKETPLACE_BONUS** (0-15 points)
Bonus selon le marketplace :

- **15 points** : Maketou ou Chariow (marketplaces africains populaires)
- **10 points** : Systeme.io
- **0 point** : Autres marketplaces

### 📊 Exemples de calcul

#### Exemple 1 : Produit Winner fort
- 8 annonces Facebook Ads
- 3 pays ciblés (Sénégal, Côte d'Ivoire, Mali)
- 2 pages publicitaires différentes
- Prix: 15,000 FCFA
- Titre présent
- Description avec "bonus"
- CTA détecté
- Marketplace: Maketou

**Calcul:**
```
ad_score = min(40, 8*4) + min(10, 3*2) + min(10, 2*2)
         = 32 + 6 + 4 = 42 points

landing_score = 15 (prix attractif) + 10 (titre) + 5 (bonus) + 5 (CTA) + 5 (niche)
              = 40 points

marketplace_bonus = 15 (Maketou)

winner_score = min(100, 42 + 40 + 15) = 97 points ✅ WINNER FORT
```

#### Exemple 2 : Produit Winner moyen
- 3 annonces Facebook Ads
- 2 pays ciblés
- 1 page publicitaire
- Prix: 25,000 FCFA
- Titre présent
- Pas de bonus
- Pas de CTA
- Marketplace: Chariow

**Calcul:**
```
ad_score = min(40, 3*4) + min(10, 2*2) + min(10, 1*2)
         = 12 + 4 + 2 = 18 points

landing_score = 15 (prix attractif) + 10 (titre) + 0 (pas bonus) + 0 (pas CTA) + 5 (niche)
              = 30 points

marketplace_bonus = 15 (Chariow)

winner_score = min(100, 18 + 30 + 15) = 63 points ✅ WINNER MOYEN
```

#### Exemple 3 : Produit faible (score = 0)
- 0 annonces Facebook Ads (pas détecté dans les ads)
- Pas de prix
- Pas de titre

**Calcul:**
```
ad_score = 0 (pas d'annonces)

landing_score = 0 (pas de prix) + 0 (pas de titre) + 0 + 0 + 5 (niche)
              = 5 points

marketplace_bonus = 0 (marketplace inconnu)

winner_score = min(100, 0 + 5 + 0) = 5 points ❌ PAS UN WINNER
```

## 🏆 Seuils de qualification

- **Score = 0** : ❌ **NON AFFICHÉ** - Produit non qualifié (pas d'annonces, pas de données)
- **Score 1-49** : ❌ **NON AFFICHÉ** - Produit faible, pas assez crédible
- **Score 50-69** : ✅ **WINNER FAIBLE** - Opportunité moyenne (seuil minimum d'affichage)
- **Score 70-84** : ✅✅ **WINNER MOYEN** - Bonne opportunité
- **Score 85-100** : ✅✅✅ **WINNER FORT** - Excellente opportunité

## 🔄 Critères pour être un "Winner" (affiché)

Un produit est considéré comme "winner" et **AFFICHÉ** s'il a **AU MINIMUM** :

1. ✅ **Score >= 50** (seuil de crédibilité)
2. ✅ **Au moins 2-3 annonces Facebook Ads** détectées
3. ✅ **Un prix défini** (mieux si entre 5K-30K FCFA)
4. ✅ **Un titre de produit** clair
5. ✅ **Présent sur un marketplace connu** (Maketou, Chariow, Systeme.io)

### 📊 Pourquoi score minimum = 50 ?

Un score de 50 implique généralement :
- **Au moins 2-3 annonces Facebook Ads** (8-12 points)
- **1-2 pays ciblés** (2-4 points)
- **Prix défini** (8-15 points)
- **Titre + niche** (15 points)
- **Bonus marketplace** (10-15 points)
- **Total ≈ 50 points minimum**

Cela garantit que seuls les produits avec une **vraie présence publicitaire** et une **landing page correcte** sont affichés.

## 🎯 Pourquoi ce système ?

Le scoring est basé sur des **signaux observables** :

1. **Plusieurs annonces = produit qui marche**
   - Si un vendeur investit dans plusieurs annonces pour le même produit, c'est qu'il génère des ventes

2. **Plusieurs pays = produit scalable**
   - Un produit qui marche dans plusieurs pays d'Afrique de l'Ouest est un bon signal

3. **Prix attractif = sweet spot**
   - Les prix entre 5K-30K FCFA sont les plus convertisseurs en Afrique

4. **Marketplace connu = confiance**
   - Maketou et Chariow sont des marketplaces populaires en Afrique

## 🔧 Améliorations possibles

Le système actuel est **simple et heuristique**. On pourrait l'améliorer avec :

1. **Durée de vie des annonces** (actuellement placeholder à 30 jours)
2. **Similarité des textes d'annonces** (si plusieurs annonces similaires = scaling)
3. **Présence de preuves sociales** (témoignages, chiffres de vente)
4. **Analyse des commentaires** Facebook Ads
5. **Tendances temporelles** (score qui augmente dans le temps = bon signal)
