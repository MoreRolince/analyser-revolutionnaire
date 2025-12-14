"""
Script simplifié pour lancer le pipeline Facebook Ads
"""
import asyncio
import sys
import os

# S'assurer que le chemin est correct
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

# Importer et lancer le pipeline
from facebook_ads_pipeline import main

if __name__ == "__main__":
    print("🚀 Lancement du pipeline Facebook Ads...")
    print("=" * 70)
    asyncio.run(main())


Script simplifié pour lancer le pipeline Facebook Ads
"""
import asyncio
import sys
import os

# S'assurer que le chemin est correct
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

# Importer et lancer le pipeline
from facebook_ads_pipeline import main

if __name__ == "__main__":
    print("🚀 Lancement du pipeline Facebook Ads...")
    print("=" * 70)
    asyncio.run(main())

