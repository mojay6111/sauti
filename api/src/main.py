"""
main.py — FastAPI application factory.
"""

import os
import sys
import time
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from loguru import logger
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address

ROOT = Path(__file__).parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "ml"))

from api.src.routes.analyze import router as analyze_router
from api.src.routes.feedback import router as feedback_router
from api.src.routes.health import router as health_router

limiter = Limiter(key_func=get_remote_address, default_limits=["60/minute"])


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting Sauti API...")
    app.state.model = None
    app.state.cleaner = None
    app.state.model_version = "none"
    app.state.start_time = time.time()

    try:
        from ml.src.data.cleaner import TextCleaner
        from ml.src.models.baseline import BaselineClassifier

        app.state.cleaner = TextCleaner()

        model_dir = ROOT / "ml" / "runs"
        model_files = sorted(model_dir.glob("baseline_*.pkl"), reverse=True) if model_dir.exists() else []

        if model_files:
            latest = model_files[0]
            logger.info(f"Loading model: {latest.name}")
            app.state.model = BaselineClassifier.load(latest)
            app.state.model_version = latest.stem
        else:
            logger.warning("No saved model found — training from seed data...")
            app.state.model, app.state.model_version = _train_from_seed()

    except Exception as e:
        logger.error(f"Model load failed: {e}")

    logger.success("Sauti API ready.")
    yield
    logger.info("Shutting down.")


def _train_from_seed():
    from ml.src.data.cleaner import TextCleaner
    from ml.src.models.baseline import BaselineClassifier
    from ml.src.data.loader import SautiDataset, ALL_LABELS
    from sklearn.preprocessing import MultiLabelBinarizer

    seed_path = ROOT / "annotation" / "seed_examples" / "pilot_dataset.csv"
    ds = SautiDataset(seed_path).load()
    df = ds.df.copy()

    mlb = MultiLabelBinarizer(classes=ALL_LABELS)
    y = mlb.fit_transform(df["labels"])
    cleaner = TextCleaner()
    X = [cleaner.clean(t)["cleaned"] for t in df["text"].tolist()]

    model = BaselineClassifier(labels=ALL_LABELS).build().train(X, y)
    version = "baseline_seed_v1"

    save_path = ROOT / "ml" / "runs" / f"{version}.pkl"
    save_path.parent.mkdir(parents=True, exist_ok=True)
    model.save(save_path)
    return model, version


def create_app() -> FastAPI:
    app = FastAPI(
        title="Sauti API",
        description="Harmful Speech Detection for East Africa — Swahili, Sheng, English",
        version="0.1.0",
        lifespan=lifespan,
    )

    app.state.limiter = limiter
    app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

    allowed_origins = os.getenv(
        "ALLOWED_ORIGINS",
        "http://localhost:3000,https://sauti.africa"
    ).split(",")

    app.add_middleware(
        CORSMiddleware,
        allow_origins=allowed_origins,
        allow_credentials=True,
        allow_methods=["GET", "POST"],
        allow_headers=["*"],
    )

    @app.middleware("http")
    async def log_requests(request: Request, call_next):
        start = time.perf_counter()
        response = await call_next(request)
        ms = int((time.perf_counter() - start) * 1000)
        logger.info(f"{request.method} {request.url.path} → {response.status_code} ({ms}ms)")
        return response

    @app.exception_handler(Exception)
    async def global_error_handler(request: Request, exc: Exception):
        logger.error(f"Unhandled error: {exc}")
        return JSONResponse(status_code=500, content={"detail": "Internal server error."})

    app.include_router(health_router)
    app.include_router(analyze_router, prefix="/v1")
    app.include_router(feedback_router, prefix="/v1")

    return app


app = create_app()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=int(os.getenv("PORT", 8000)),
        reload=os.getenv("ENV", "development") == "development",
    )
