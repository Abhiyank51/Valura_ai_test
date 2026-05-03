from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

app = FastAPI(
    title="Valura AI Portfolio Copilot",
    description="Build, monitor, grow, and protect your portfolio.",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/health")
@app.get("/v1/health")
async def health_check():
    return JSONResponse(content={"status": "ok"})

@app.get("/dashboard")
async def dashboard():
    from fastapi.responses import FileResponse
    return FileResponse(os.path.join(os.path.dirname(__file__), "static", "index.html"))

from fastapi.staticfiles import StaticFiles
import os

from src.api.routes import router
app.include_router(router)

static_path = os.path.join(os.path.dirname(__file__), "static")
app.mount("/", StaticFiles(directory=static_path, html=True), name="static")
