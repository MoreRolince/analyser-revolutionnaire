from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from contextlib import asynccontextmanager
import os
from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv

from app.database import engine, Base, SessionLocal
from app.routers import auth, users, analyse, shops, products, favorites, admin, dashboard, winners, scraper, market_stats
from sqlalchemy import text

load_dotenv()

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    Base.metadata.create_all(bind=engine)
    yield
    # Shutdown
    pass

app = FastAPI(
    title="MarketPulse Africa API",
    description="API backend pour le SaaS MarketPulse Africa",
    version="1.0.0",
    lifespan=lifespan
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:3001", "http://127.0.0.1:3000", "http://127.0.0.1:3001"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Routers
app.include_router(auth.router, prefix="/api/v1/auth", tags=["auth"])
app.include_router(users.router, prefix="/api/v1/users", tags=["users"])
app.include_router(dashboard.router, prefix="/api/v1/dashboard", tags=["dashboard"])
app.include_router(analyse.router, prefix="/api/v1/analyse", tags=["analyse"])
app.include_router(shops.router, prefix="/api/v1/shops", tags=["shops"])
app.include_router(products.router, prefix="/api/v1/products", tags=["products"])
app.include_router(favorites.router, prefix="/api/v1/favorites", tags=["favorites"])
app.include_router(winners.router, prefix="/api/v1/winners", tags=["winners"])
app.include_router(admin.router, prefix="/api/v1/admin", tags=["admin"])
app.include_router(scraper.router, prefix="/api/v1/scraper", tags=["scraper"])
app.include_router(market_stats.router, prefix="/api/v1/market-stats", tags=["market-stats"])

# Servir les fichiers uploadés
upload_dir = Path("uploads")
upload_dir.mkdir(exist_ok=True)
app.mount("/uploads", StaticFiles(directory=str(upload_dir)), name="uploads")

@app.get("/")
async def root():
    return {"message": "MarketPulse Africa API", "version": "1.0.0"}

@app.get("/health")
async def health():
    """Endpoint de santé qui vérifie la connexion à la base de données"""
    try:
        db = SessionLocal()
        try:
            # Test simple de connexion à la base de données
            db.execute(text("SELECT 1"))
            return {
                "status": "healthy",
                "database": "connected",
                "timestamp": datetime.now().isoformat()
            }
        finally:
            db.close()
    except Exception as e:
        return JSONResponse(
            status_code=503,
            content={
                "status": "unhealthy",
                "database": "disconnected",
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
        )

