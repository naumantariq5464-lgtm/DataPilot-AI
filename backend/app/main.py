import os
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.routers import auth, datasets, analysis


# ── Lifespan — startup / shutdown logic ──────────────────────────────────────

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: ensure temp directory exists
    os.makedirs(settings.temp_dir, exist_ok=True)
    print(f"[DataPilot] Temp directory ready: {settings.temp_dir}")
    print(f"[DataPilot] Environment: {settings.app_env}")
    print(f"[DataPilot] AI Model: {settings.vultr_model_name}")
    yield
    # Shutdown: nothing to clean up at app level
    print("[DataPilot] Shutting down.")


# ── App instance ─────────────────────────────────────────────────────────────

app = FastAPI(
    title="DataPilot AI",
    description="AI-powered autonomous data analysis platform.",
    version="1.0.0",
    lifespan=lifespan,
    # Disable auto docs in production
    docs_url="/docs" if settings.app_env == "development" else None,
    redoc_url="/redoc" if settings.app_env == "development" else None,
)


# ── CORS ─────────────────────────────────────────────────────────────────────

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "DELETE"],
    allow_headers=["Authorization", "Content-Type"],
)


# ── Routers ──────────────────────────────────────────────────────────────────

app.include_router(auth.router,     prefix="/auth",     tags=["Auth"])
app.include_router(datasets.router, prefix="/datasets", tags=["Datasets"])
app.include_router(analysis.router, prefix="/analysis", tags=["Analysis"])


# ── Health Check ─────────────────────────────────────────────────────────────

@app.get("/health", tags=["Health"])
async def health_check():
    return {
        "status": "ok",
        "app": "DataPilot AI",
        "environment": settings.app_env,
        "model": settings.vultr_model_name,
    }
