from pathlib import Path

from dotenv import load_dotenv


env_path = (
    Path(__file__).resolve().parent.parent
    / ".env"
)

load_dotenv(dotenv_path=env_path)


from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.routers import creative_agent_router
from app.routers import local_generation_router


app = FastAPI(
    title="PRANA Creative Intelligence API",
    version="2.0.0",
)


app.include_router(
    creative_agent_router.router,
    prefix="/api/v1/creative-agent",
    tags=["creative-agent"],
)

app.include_router(
    creative_agent_router.app_router,
    prefix="/api/v1",
    tags=["app"],
)

app.include_router(
    local_generation_router.router,
    prefix="/api/local-generation",
    tags=["local-generation"],
)


generated_dir = (
    Path(__file__).resolve().parent.parent
    / "generated"
)

generated_dir.mkdir(
    parents=True,
    exist_ok=True,
)

app.mount(
    "/generated",
    StaticFiles(directory=str(generated_dir)),
    name="generated",
)


app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
async def root():
    return {
        "message": (
            "PRANA Creative Intelligence API"
        )
    }


@app.get("/api/health")
async def health_check():
    return {
        "status": "healthy",
        "service": "prana-api",
    }