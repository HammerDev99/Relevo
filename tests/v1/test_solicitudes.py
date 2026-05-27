from datetime import date

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import StaticPool, create_engine
from sqlalchemy.orm import sessionmaker

from app.auth import get_password_hash
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

@pytest.fixture
def auth_client(client, db_session):
    # Create employee and backup
    h = get_password_hash("pass123")
    emp = Empleado(nombre="Juan", correo="juan@test.com", password_hash=h)
    resp = Empleado(nombre="Respaldo", correo="resp@test.com", password_hash=h)
    db_session.add_all([emp, resp])
    db_session.commit()
    
    # Login
    client.post("/login", data={"correo": "juan@test.com", "password": "pass123"})
    return client, emp, resp

def test_crear_solicitud_vacaciones_exitosa(auth_client, db_session):
    client, emp, resp = auth_client
    
    data = {
        "tipo": "vacaciones",
        "fecha_inicio": "2026-12-01",
        "fecha_fin": "2026-12-05",
        "respaldo_id": resp.id
    }
    
    response = client.post("/solicitudes/nueva", data=data)
    assert response.status_code == 200
    assert response.json()["estado"] == "pendiente"
    
    # Verify in DB
    solicitud = db_session.query(Solicitud).first()
    assert solicitud is not None
    assert solicitud.empleado_id == emp.id
    assert solicitud.dias_habiles > 0

def test_crear_solicitud_concurrencia_violada(auth_client, db_session):
    client, emp, resp = auth_client
    
    # Pre-existing approved solicitud from another user
    h = get_password_hash("h")
    otra_persona = Empleado(nombre="Otro", correo="otro@test.com", password_hash=h)
    db_session.add(otra_persona)
    db_session.commit()
    
    s1 = Solicitud(
        empleado_id=otra_persona.id,
        tipo="vacaciones",
        fecha_inicio=date(2026, 12, 1),
        fecha_fin=date(2026, 12, 10),
        dias_habiles=8,
        estado="aprobada",
        respaldo_id=resp.id
    )
    db_session.add(s1)
    db_session.commit()
    
    # Current user tries to overlap
    data = {
        "tipo": "vacaciones",
        "fecha_inicio": "2026-12-05",
        "fecha_fin": "2026-12-12",
        "respaldo_id": resp.id
    }
    
    response = client.post("/solicitudes/nueva", data=data)
    # Domain error should be handled, returning 400 or showing in UI (for now 400)
    assert response.status_code == 400
    assert "Cupo lleno" in response.json()["detail"]

def test_listar_mis_solicitudes(auth_client, db_session):
    client, emp, resp = auth_client
    
    # Create one for me and one for another
    h = get_password_hash("h")
    otra_persona = Empleado(nombre="Otro", correo="otro@test.com", password_hash=h)
    db_session.add(otra_persona)
    db_session.commit()
    
    s1 = Solicitud(empleado_id=emp.id, tipo="vacaciones", fecha_inicio=date(2026, 1, 1), 
                   fecha_fin=date(2026, 1, 5), dias_habiles=5, respaldo_id=resp.id)
    s2 = Solicitud(empleado_id=otra_persona.id, tipo="vacaciones", fecha_inicio=date(2026, 1, 1), 
                   fecha_fin=date(2026, 1, 5), dias_habiles=5, respaldo_id=resp.id)
    db_session.add_all([s1, s2])
    db_session.commit()
    
    response = client.get("/solicitudes")
    assert response.status_code == 200
    items = response.json()
    assert len(items) == 1
    assert items[0]["empleado_id"] == emp.id
