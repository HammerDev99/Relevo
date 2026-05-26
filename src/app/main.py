from contextlib import asynccontextmanager

from fastapi import FastAPI
from src.app.database import init_db
from src.app.routes import auth, disponibilidad, solicitudes


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Initialize DB
    init_db()
    yield
    # Shutdown: Clean up if needed

app = FastAPI(title="Relevo API", lifespan=lifespan)

# Incluir rutas
app.include_router(auth.router)
app.include_router(solicitudes.router)
app.include_router(disponibilidad.router)

@app.get("/")
def read_root():
    return {"message": "Relevo API v1"}
