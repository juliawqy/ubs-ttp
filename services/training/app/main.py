from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routers import modules, career_mapping, iat

app = FastAPI(title="aequus-training", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # tighten in production via env var
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


app.include_router(modules.router)
app.include_router(career_mapping.router)
app.include_router(iat.router)


@app.get("/health")
def health():
    return {"status": "ok", "service": "training"}
