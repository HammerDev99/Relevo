from datetime import date

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import StaticPool, create_engine
from sqlalchemy.orm import sessionmaker

from app.database import Base, get_db
from app.main import app
from app.models import Empleado, Solicitud

# In-memory engine shared for tests
test_engine = create_engine(
    "sqlite:///:memory:",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)

@pytest.fixture(scope="session", autouse=True)
def setup_db():
    Base.metadata.create_all(bind=test_engine)
    yield
    Base.metadata.drop_all(bind=test_engine)

@pytest.fixture
def db_session():
    db = TestingSessionLocal()
    def override_get_db():
        try:
            yield db
        finally:
            pass
    app.dependency_overrides[get_db] = override_get_db
    try:
        yield db
    finally:
        for table in reversed(Base.metadata.sorted_tables):
            db.execute(table.delete())
        db.commit()
        db.close()
        app.dependency_overrides.clear()

@pytest.fixture
def client():
    return TestClient(app)

def test_disponibilidad_sin_pii(client, db_session):
    # Setup: 1 approved standard, 1 approved exception
    emp1 = Empleado(nombre="Juan PII", correo="juan@test.com", password_hash="h")
    emp2 = Empleado(nombre="Maria PII", correo="maria@test.com", password_hash="h")
    db_session.add_all([emp1, emp2])
    db_session.commit()

    # Juan is away (standard)
    s1 = Solicitud(
        empleado_id=emp1.id, 
        tipo="vacaciones", 
        fecha_inicio=date(2026, 1, 1), 
        fecha_fin=date(2026, 1, 2), 
        dias_habiles=2,
        estado="aprobada"
    )
    # Maria is away (exception)
    s2 = Solicitud(
        empleado_id=emp2.id, 
        tipo="permiso", 
        fecha_inicio=date(2026, 1, 2), 
        fecha_fin=date(2026, 1, 3), 
        dias_habiles=2,
        estado="aprobada",
        es_excepcion=True
    )
    db_session.add_all([s1, s2])
    db_session.commit()

    response = client.get("/disponibilidad?anio=2026&mes=1")
    assert response.status_code == 200
    data = response.json()
    
    # 2026-01-01 should be OCUPADO (Juan standard)
    day1 = next(d for d in data if d["fecha"] == "2026-01-01")
    assert day1["estado"] == "OCUPADO"
    
    # 2026-01-02 should be EXCEPCIONAL (Juan + Maria)
    day2 = next(d for d in data if d["fecha"] == "2026-01-02")
    assert day2["estado"] == "EXCEPCIONAL"
    
    # Verify NO PII
    str_response = response.text
    assert "Juan" not in str_response
    assert "Maria" not in str_response
    assert "PII" not in str_response
    assert "juan@test.com" not in str_response
