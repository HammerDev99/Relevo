from fastapi import FastAPI
from src.app.database import init_db
from src.app.routes import auth

app = FastAPI(title="Relevo API")

# Incluir rutas
app.include_router(auth.router)

@app.get("/")
def read_root():
    return {"message": "Relevo API v1"}

# Opcional: inicializar BD al arrancar (simplificado para MVP)
@app.on_event("startup")
def on_startup():
    init_db()
