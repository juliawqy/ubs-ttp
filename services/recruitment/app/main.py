from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routers import candidates, job_postings, interviews

app = FastAPI(title="ubs-ttp-recruitment", version="0.1.0", redirect_slashes=False)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # tighten in production via env var
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


app.include_router(candidates.router)
app.include_router(job_postings.router)
app.include_router(interviews.router)


@app.get("/health")
def health():
    return {"status": "ok", "service": "recruitment"}
