
from fastapi import FastAPI
from fastapi.responses import FileResponse
from pathlib import Path

from app.routes.calculator import router

app = FastAPI(
    title="CALCI - Stack Based Calculator",
    description="Full-stack calculator powered by Stack Data Structure",
    version="1.0.0"
)

BASE_DIR = Path(__file__).resolve().parent


@app.get("/")
def home():
    return FileResponse(BASE_DIR / "static" / "index.html")


@app.get("/health")
def health():
    return {"status": "healthy"}


app.include_router(router)
