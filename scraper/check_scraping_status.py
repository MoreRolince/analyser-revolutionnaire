"""
Vérifier l'état du scraping en cours
"""
import os
import sys
from sqlalchemy import create_engine, text
from datetime import datetime

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://marketpulse:marketpulse_password@localhost:5433/marketpulse"
)

engine = create_engine(DATABASE_URL)
conn = engine.connect()

print("=" * 70)
print("ETAT DU SCRAPING")
print("=" * 70)

# Vérifier les annonces
result = conn.execute(text("""
    SELECT 
        COUNT(*) as total,
        COUNT(CASE WHEN scraped_at > NOW() - INTERVAL '1 hour' THEN 1 END) as dernieres_heure,
        COUNT(CASE WHEN scraped_at > NOW() - INTERVAL '10 minutes' THEN 1 END) as dernieres_10min,
        MAX(scraped_at) as dernier_scraping
    FROM fb_ads_raw
"""))
row = result.fetchone()

print(f"\nANNONCES:")
print(f"  Total: {row[0]}")
print(f"  Dernieres heure: {row[1]}")
print(f"  Dernieres 10 min: {row[2]}")
print(f"  Dernier scraping: {row[3]}")

# Vérifier les produits
result = conn.execute(text("""
    SELECT 
        COUNT(*) as total,
        MAX(created_at) as dernier_produit
    FROM digital_products_detected
"""))
row = result.fetchone()

print(f"\nPRODUITS:")
print(f"  Total: {row[0]}")
print(f"  Dernier produit: {row[1]}")

# Vérifier les scores
result = conn.execute(text("""
    SELECT 
        COUNT(*) as total,
        MAX(calculated_at) as dernier_score
    FROM digital_products_scores
"""))
row = result.fetchone()

print(f"\nSCORES:")
print(f"  Total: {row[0]}")
print(f"  Dernier score: {row[1]}")

print(f"\n{'=' * 70}")
print(f"Temps actuel: {datetime.now()}")
print(f"{'=' * 70}")

conn.close()

