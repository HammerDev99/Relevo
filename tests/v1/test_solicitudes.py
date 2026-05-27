from collections.abc import Generator
from datetime import date

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import StaticPool, create_engine
from sqlalchemy.orm import Session, sessionmaker

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
def setup_db() -> None:
    Base.metadata.create_all(bind=test_engine)
    yield
    Base.metadata.drop_all(bind=test_engine)


@pytest.fixture
def db_session() -> Generator[Session, None, None]:
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
def client() -> Generator[TestClient, None, None]:
    yield TestClient(app)


@pytest.fixture
def auth_client(
    client: TestClient, db_session: Session
) -> Generator[tuple[TestClient, Empleado, Empleado], None, None]:
    # Create employee and backup
    from app.models import Grupo
    g = Grupo(nombre="G", min_presentes=0)
    db_session.add(g)

    h = get_password_hash("pass123")
    emp = Empleado(nombre="Juan", correo="juan@test.com", password_hash=h)
    resp = Empleado(nombre="Respaldo", correo="resp@test.com", password_hash=h)
    emp.grupos.append(g)
    resp.grupos.append(g)
    db_session.add_all([emp, resp])
    db_session.commit()

    # Login
    client.post("/login", data={"correo": "juan@test.com", "password": "pass123"})
    yield client, emp, resp


def test_crear_solicitud_vacaciones_exitosa(
    auth_client: tuple[TestClient, Empleado, Empleado], db_session: Session
) -> None:
    client, emp, resp = auth_client

    data = {
        "tipo": "vacaciones",
        "fecha_inicio": "2026-12-01",
        "fecha_fin": "2026-12-05",
        "respaldo_id": resp.id,
    }

    response = client.post("/solicitudes/nueva", data=data)
    assert response.status_code == 200
    assert response.json()["estado"] == "aprobada"

    # Verify in DB
    solicitud = db_session.query(Solicitud).first()
    assert solicitud is not None
    assert solicitud.empleado_id == emp.id
    assert solicitud.dias_habiles > 0


def test_crear_solicitud_concurrencia_violada(
    auth_client: tuple[TestClient, Empleado, Empleado], db_session: Session
) -> None:
    client, emp, resp = auth_client

    # Pre-existing approved solicitud from another user
    h = get_password_hash("h")
    otra_persona = Empleado(nombre="Otro", correo="otro@test.com", password_hash=h)
    from app.models import Grupo
    g_restrictivo = Grupo(nombre="Restrictivo", min_presentes=2)
    otra_persona.grupos.append(g_restrictivo)
    emp.grupos.append(g_restrictivo)
    db_session.add(g_restrictivo)
    db_session.add(otra_persona)
    db_session.commit()

    s1 = Solicitud(
        empleado_id=otra_persona.id,
        tipo="vacaciones",
        fecha_inicio=date(2026, 12, 1),
        fecha_fin=date(2026, 12, 10),
        dias_habiles=8,
        estado="aprobada",
        respaldo_id=resp.id,
    )
    db_session.add(s1)
    db_session.commit()

    # Current user tries to overlap
    data = {
        "tipo": "vacaciones",
        "fecha_inicio": "2026-12-05",
        "fecha_fin": "2026-12-12",
        "respaldo_id": resp.id,
    }

    response = client.post("/solicitudes/nueva", data=data)
    # Domain error should be handled, returning 400 or showing in UI (for now 400)
    assert response.status_code == 400
    assert "CUPO_LLENO" in response.json()["detail"]


def test_listar_mis_solicitudes(
    auth_client: tuple[TestClient, Empleado, Empleado], db_session: Session
) -> None:
    client, emp, resp = auth_client

    # Pre-existing approved solicitud from another user
    h = get_password_hash("h")
    otra_persona = Empleado(nombre="Otro", correo="otro@test.com", password_hash=h)  
    from app.models import Grupo
    g_restrictivo = Grupo(nombre="Restrictivo", min_presentes=2)
    otra_persona.grupos.append(g_restrictivo)
    emp.grupos.append(g_restrictivo)
    db_session.add(g_restrictivo)
    db_session.add(otra_persona)
    db_session.commit()
    s1 = Solicitud(
        empleado_id=emp.id,
        tipo="vacaciones",
        fecha_inicio=date(2026, 1, 1),
        fecha_fin=date(2026, 1, 5),
        dias_habiles=5,
        respaldo_id=resp.id,
    )
    s2 = Solicitud(
        empleado_id=otra_persona.id,
        tipo="vacaciones",
        fecha_inicio=date(2026, 1, 1),
        fecha_fin=date(2026, 1, 5),
        dias_habiles=5,
        respaldo_id=resp.id,
    )
    db_session.add_all([s1, s2])
    db_session.commit()

    response = client.get("/solicitudes")
    assert response.status_code == 200
    items = response.json()
    assert len(items) == 1
    assert items[0]["empleado_id"] == emp.id

def test_eliminar_solicitud_propia(
    auth_client: tuple[TestClient, Empleado, Empleado], db_session: Session
) -> None:
    client, emp, resp = auth_client

    s1 = Solicitud(
        empleado_id=emp.id,
        tipo="vacaciones",
        fecha_inicio=date(2026, 1, 1),
        fecha_fin=date(2026, 1, 5),
        dias_habiles=5,
        respaldo_id=resp.id,
    )
    db_session.add(s1)
    db_session.commit()

    solicitud_id = s1.id

    response = client.delete(f"/solicitudes/{solicitud_id}")
    assert response.status_code == 200

    # Verify it is deleted
    assert db_session.get(Solicitud, solicitud_id) is None

def test_eliminar_solicitud_ajena_falla(
    auth_client: tuple[TestClient, Empleado, Empleado], db_session: Session
) -> None:
    client, emp, resp = auth_client

    h = get_password_hash("h")
    otro = Empleado(nombre="Otro", correo="otro@test.com", password_hash=h)
    db_session.add(otro)
    db_session.commit()

    s1 = Solicitud(
        empleado_id=otro.id,
        tipo="vacaciones",
        fecha_inicio=date(2026, 1, 1),
        fecha_fin=date(2026, 1, 5),
        dias_habiles=5,
    )
    db_session.add(s1)
    db_session.commit()

    response = client.delete(f"/solicitudes/{s1.id}")
    assert response.status_code == 404


def test_crear_solicitud_sin_justificacion(
    auth_client: tuple[TestClient, Empleado, Empleado], db_session: Session
) -> None:
    """SPEC-S15-C3: Test que el backend acepta solicitudes sin justificación."""
    client, emp, resp = auth_client

    # Crear solicitud sin justificación
    response = client.post(
        "/solicitudes/nueva",
        data={
            "tipo": "vacaciones",
            "fecha_inicio": "2026-07-01",
            "fecha_fin": "2026-07-05",
            "respaldo_id": resp.id,
            "es_excepcion": False,
            "justificacion": ""  # Justificación vacía
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert data["justificacion"] is None or data["justificacion"] == ""
