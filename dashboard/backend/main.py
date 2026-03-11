"""
main.py – Clawdi Brain Dashboard FastAPI Backend
=================================================
"""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from config import CORS_ORIGINS, API_PORT
from routers import neural_feed, knowledge_vault, short_term_memory

# ── Logging ─────────────────────────────────────────────────────────────────

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s │ %(levelname)-7s │ %(name)s │ %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
log = logging.getLogger("dashboard")


# ── Lifespan ────────────────────────────────────────────────────────────────

@asynccontextmanager
async def lifespan(app: FastAPI):
    log.info("🧠 Clawdi Brain Dashboard API starting …")
    yield
    log.info("Dashboard API shutting down.")


# ── App ─────────────────────────────────────────────────────────────────────

app = FastAPI(
    title="Clawdi Brain Dashboard API",
    description="Backend API for the OpenClaw AI Memory Dashboard",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Routers
app.include_router(neural_feed.router)
app.include_router(knowledge_vault.router)
app.include_router(short_term_memory.router)


@app.get("/api/ping")
async def ping():
    return {"status": "ok", "service": "clawdi-brain-dashboard"}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("main:app", host="0.0.0.0", port=API_PORT, reload=True)
