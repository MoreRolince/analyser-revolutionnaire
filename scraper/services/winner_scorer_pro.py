"""
Système de scoring WINNER PRO - Basé sur signaux réels
"""
from typing import Dict, Any, List
from datetime import datetime, timedelta
import re


class WinnerScorerPro:
    """Scoring professionnel basé sur signaux observables"""
    
    @staticmethod
    def calculate_winner_score(
        product_data: Dict[str, Any],
        ads_data: List[Dict[str, Any]],
        landing_page_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Calcule le score WINNER (0-100) basé sur:
        - Nombre d'ads actives (même landing page)
        - Durée d'activité des ads
        - Similarité des textes (ads scalées)
        - Signaux d'engagement
        - Présence WhatsApp CTA
        - Présence payment proof
        """
        score = 0.0
        details = {}
        
        # 1. SCORE PAR NOMBRE D'ADS (0-30 points)
        ads_count = len(ads_data)
        if ads_count >= 5:
            ads_score = 30
        elif ads_count >= 3:
            ads_score = 20
        elif ads_count >= 2:
            ads_score = 10
        else:
            ads_score = 5
        
        score += ads_score
        details['ads_count_score'] = ads_score
        details['ads_count'] = ads_count
        
        # 2. SCORE PAR DURÉE D'ACTIVITÉ (0-25 points)
        duration_score = WinnerScorerPro._calculate_duration_score(ads_data)
        score += duration_score
        details['duration_score'] = duration_score
        
        # 3. SCORE PAR SIMILARITÉ DES TEXTES (0-15 points)
        # Si plusieurs ads avec texte similaire = scaling = winner signal
        similarity_score = WinnerScorerPro._calculate_text_similarity_score(ads_data)
        score += similarity_score
        details['similarity_score'] = similarity_score
        
        # 4. SCORE PAR SIGNAUX AFRICAINS (0-10 points)
        africa_score = WinnerScorerPro._calculate_africa_relevance_score(ads_data, product_data)
        score += africa_score
        details['africa_relevance_score'] = africa_score
        
        # 5. SCORE PAR WHATSAPP CTA (0-10 points)
        whatsapp_score = WinnerScorerPro._calculate_whatsapp_score(ads_data, landing_page_data)
        score += whatsapp_score
        details['whatsapp_score'] = whatsapp_score
        
        # 6. SCORE PAR PAYMENT PROOF (0-10 points)
        payment_proof_score = WinnerScorerPro._calculate_payment_proof_score(ads_data)
        score += payment_proof_score
        details['payment_proof_score'] = payment_proof_score
        
        # Limiter à 100
        final_score = min(100.0, score)
        
        return {
            'winner_score': final_score,
            'ads_count': ads_count,
            'scoring_details': details,
        }
    
    @staticmethod
    def _calculate_duration_score(ads_data: List[Dict[str, Any]]) -> float:
        """Calcule le score basé sur la durée d'activité"""
        # Si on a des dates de scraped_at, calculer la durée
        # Sinon, estimer basé sur le nombre d'ads (plus d'ads = plus long)
        ads_count = len(ads_data)
        
        if ads_count >= 5:
            return 25  # >30 jours probablement
        elif ads_count >= 3:
            return 15  # >14 jours
        elif ads_count >= 2:
            return 8   # >7 jours
        else:
            return 3   # <7 jours
    
    @staticmethod
    def _calculate_text_similarity_score(ads_data: List[Dict[str, Any]]) -> float:
        """Calcule le score basé sur la similarité des textes (scaling)"""
        if len(ads_data) < 2:
            return 0
        
        texts = [ad.get('ad_text', '')[:100] for ad in ads_data if ad.get('ad_text')]
        
        if len(texts) < 2:
            return 0
        
        # Compter les mots communs
        common_words = set()
        for i, text1 in enumerate(texts):
            words1 = set(text1.lower().split())
            for text2 in texts[i+1:]:
                words2 = set(text2.lower().split())
                common = words1.intersection(words2)
                if len(common) >= 5:  # Au moins 5 mots communs
                    common_words.update(common)
        
        if len(common_words) >= 10:
            return 15  # Textes très similaires = scaling
        elif len(common_words) >= 5:
            return 8   # Textes similaires
        else:
            return 3   # Textes différents
    
    @staticmethod
    def _calculate_africa_relevance_score(ads_data: List[Dict[str, Any]], product_data: Dict[str, Any]) -> float:
        """Calcule le score de pertinence africaine"""
        score = 0.0
        
        # Vérifier dans les ads
        for ad in ads_data:
            text = (ad.get('ad_text', '') + ' ' + ad.get('landing_page_url', '')).lower()
            
            if 'fcfa' in text or 'xof' in text:
                score += 2
            if 'orange money' in text or 'mtn momo' in text:
                score += 2
            if any(country in text for country in ['bénin', 'côte d\'ivoire', 'cameroun', 'sénégal']):
                score += 2
        
        # Vérifier dans le produit
        product_text = (product_data.get('description', '') + ' ' + product_data.get('landing_page_url', '')).lower()
        if 'fcfa' in product_text:
            score += 2
        
        return min(10.0, score)
    
    @staticmethod
    def _calculate_whatsapp_score(ads_data: List[Dict[str, Any]], landing_page_data: Dict[str, Any]) -> float:
        """Calcule le score basé sur la présence de WhatsApp CTA"""
        score = 0.0
        
        # Vérifier dans les ads
        for ad in ads_data:
            if ad.get('has_whatsapp_cta'):
                score += 3
        
        # Vérifier dans la landing page
        if landing_page_data.get('has_whatsapp_funnel'):
            score += 5
        
        return min(10.0, score)
    
    @staticmethod
    def _calculate_payment_proof_score(ads_data: List[Dict[str, Any]]) -> float:
        """Calcule le score basé sur la présence de preuves de paiement"""
        score = 0.0
        
        for ad in ads_data:
            if ad.get('has_payment_proof'):
                score += 5
        
        return min(10.0, score)

