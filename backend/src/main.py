from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.api.company import router as company_router
from src.api.message import router as message_router

app = FastAPI(title="Sparkstral")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(message_router, prefix="/api")
app.include_router(company_router, prefix="/api")


@app.get("/api/health")
def health() -> dict[str, str]:
    return {"status": "ok"}
