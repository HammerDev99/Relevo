from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.database import init_db
from app.routes import auth, coordinacion, disponibilidad, solicitudes


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    # Startup: Initialize DB
    init_db()
    yield
    # Shutdown: Clean up if needed

app = FastAPI(title="Relevo API", lifespan=lifespan)

# Incluir rutas
app.include_router(auth.router)
app.include_router(solicitudes.router)
app.include_router(disponibilidad.router)
app.include_router(coordinacion.router)

@app.get("/")
def read_root() -> dict[str, str]:
    return {"message": "Relevo API v1"}
