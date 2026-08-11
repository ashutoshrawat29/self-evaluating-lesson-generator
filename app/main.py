from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.api.lessons import router
from app.memory.database import initialize_database


@asynccontextmanager
async def lifespan(app: FastAPI):

    initialize_database()

    yield


app = FastAPI(
    title="Self-Evaluating Lesson Generator",
    description=(
        "Agentic system for generating and "
        "self-evaluating educational content."
    ),
    version="1.0.0",
    lifespan=lifespan,
)


app.include_router(router)


@app.get("/health")
def health():

    return {
        "status": "healthy"
    }