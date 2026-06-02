import os
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.database import init_db
from app.routes import auth, configuracion, coordinacion, disponibilidad, solicitudes


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    init_db()
    yield

# Deshabilitar /docs y /redoc en producción (APP_ENV=production lo setea EasyPanel)
_en_produccion = os.getenv("APP_ENV", "development") == "production"

app = FastAPI(
    title="Relevo API",
    lifespan=lifespan,
    docs_url=None if _en_produccion else "/docs",
    redoc_url=None if _en_produccion else "/redoc",
    openapi_url=None if _en_produccion else "/openapi.json",
)

# Incluir rutas
app.include_router(auth.router)
app.include_router(solicitudes.router)
app.include_router(disponibilidad.router)
app.include_router(coordinacion.router)
app.include_router(configuracion.router)

@app.get("/")
def read_root() -> dict[str, str]:
    return {"message": "Relevo API v1"}
