from urllib.parse import urlparse

def detect_marketplace(url: str) -> str:
    """
    Détecte le type de marketplace à partir de l'URL
    """
    parsed = urlparse(url)
    domain = parsed.netloc.lower()
    
    if "chariow" in domain:
        return "chariow"
    elif "maketou" in domain:
        return "maketou"
    elif "system.io" in domain or "systemio" in domain:
        return "systemio"
    else:
        return "other"

