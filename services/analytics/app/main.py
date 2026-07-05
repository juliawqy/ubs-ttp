from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routers.metrics import router as metrics_router

app = FastAPI(title="aequus-analytics", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # tighten in production via env var
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(metrics_router)


@app.get("/health")
def health():
    return {"status": "ok", "service": "analytics"}
