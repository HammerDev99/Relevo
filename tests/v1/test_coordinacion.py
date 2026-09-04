from collections.abc import Generator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import StaticPool, create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.auth import get_password_hash
from app.database import Base, get_db
from app.main import app
from app.models import Empleado

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
def admin_client(
    client: TestClient, db_session: Session
) -> Generator[tuple[TestClient, Empleado], None, None]:
    h = get_password_hash("admin123")
    admin = Empleado(nombre="Admin", correo="admin@test.com", password_hash=h, rol="coordinacion")
    db_session.add(admin)
    db_session.commit()
    client.post("/login", data={"correo": "admin@test.com", "password": "admin123"})
    yield client, admin

def test_coordinacion_eliminar_usuario(
    admin_client: tuple[TestClient, Empleado], db_session: Session
) -> None:
    client, admin = admin_client
    
    # Arrange: crear un empleado con solicitud
    from datetime import date

    from app.models import Solicitud
    h = get_password_hash("123")
    empleado = Empleado(nombre="To Delete", correo="del@test.com", password_hash=h)
    db_session.add(empleado)
    db_session.commit()
    
    solicitud = Solicitud(
        empleado_id=empleado.id,
        tipo="permiso",
        fecha_inicio=date(2026, 6, 1),
        fecha_fin=date(2026, 6, 1),
        dias_habiles=1
    )
    db_session.add(solicitud)
    db_session.commit()
    
    emp_id = empleado.id
    
    # Act: llamar al endpoint DELETE
    res = client.delete(f"/coordinacion/usuarios/{emp_id}")
    
    # Assert
    assert res.status_code == 200
    assert db_session.get(Empleado, emp_id) is None
    # Verifica el borrado en cascada
    assert db_session.query(Solicitud).filter_by(empleado_id=emp_id).first() is None


# --- SPEC-S18-B5: Alta de usuarios desde Coordinación ---

def test_crear_usuario_exitoso(
    admin_client: tuple[TestClient, Empleado], db_session: Session
) -> None:
    """SPEC-S18-B2: coordinación crea un empleado; el hash permite iniciar sesión."""
    from app.auth import verify_password

    client, _ = admin_client

    res = client.post("/coordinacion/usuarios", json={
        "nombre": "MARIANA",
        "correo": "mariana@test.com",
        "password": "Relevo2026*",
        "rol": "empleado",
        "grupo_ids": [],
    })

    assert res.status_code == 200
    body = res.json()
    assert body["nombre"] == "MARIANA"
    assert body["rol"] == "empleado"
    assert body["activo"] is True
    # El hash nunca viaja en la respuesta
    assert "password" not in body
    assert "password_hash" not in body

    creado = db_session.query(Empleado).filter_by(correo="mariana@test.com").first()
    assert creado is not None
    assert verify_password("Relevo2026*", creado.password_hash)
    assert creado.password_hash != "Relevo2026*"


def test_crear_usuario_con_grupos(
    admin_client: tuple[TestClient, Empleado], db_session: Session
) -> None:
    """SPEC-S18-B2: los grupo_ids asignan la relación M:N."""
    from app.models import Grupo

    client, _ = admin_client
    g = Grupo(nombre="G_Alta", min_presentes=1)
    db_session.add(g)
    db_session.commit()

    res = client.post("/coordinacion/usuarios", json={
        "nombre": "ROSA",
        "correo": "rosa@test.com",
        "password": "Relevo2026*",
        "rol": "empleado",
        "grupo_ids": [g.id],
    })

    assert res.status_code == 200
    assert res.json()["grupo_ids"] == [g.id]

    creado = db_session.query(Empleado).filter_by(correo="rosa@test.com").first()
    assert creado is not None
    assert [gr.nombre for gr in creado.grupos] == ["G_Alta"]


def test_crear_usuario_correo_duplicado(
    admin_client: tuple[TestClient, Empleado], db_session: Session
) -> None:
    """SPEC-S18-B2 (Failure): correo repetido → 400, no IntegrityError."""
    client, _ = admin_client
    db_session.add(Empleado(
        nombre="EXISTENTE", correo="repetido@test.com", password_hash="h"
    ))
    db_session.commit()

    res = client.post("/coordinacion/usuarios", json={
        "nombre": "OTRO",
        "correo": "repetido@test.com",
        "password": "Relevo2026*",
        "rol": "empleado",
        "grupo_ids": [],
    })

    assert res.status_code == 400
    assert "correo" in res.json()["detail"].lower()


def test_crear_usuario_requiere_coordinacion(
    client: TestClient, db_session: Session
) -> None:
    """SPEC-S18-B2 (Failure): un empleado sin rol coordinación recibe 403."""
    db_session.add(Empleado(
        nombre="Raso",
        correo="raso@test.com",
        password_hash=get_password_hash("raso1234"),
        rol="empleado",
    ))
    db_session.commit()
    client.post("/login", data={"correo": "raso@test.com", "password": "raso1234"})

    res = client.post("/coordinacion/usuarios", json={
        "nombre": "INTRUSO",
        "correo": "intruso@test.com",
        "password": "Relevo2026*",
        "rol": "coordinacion",
        "grupo_ids": [],
    })

    assert res.status_code == 403
    assert db_session.query(Empleado).filter_by(correo="intruso@test.com").first() is None


def test_crear_usuario_password_corta(
    admin_client: tuple[TestClient, Empleado], db_session: Session
) -> None:
    """SPEC-S18-B1 (Failure): contraseña de menos de 8 caracteres → 422."""
    client, _ = admin_client

    res = client.post("/coordinacion/usuarios", json={
        "nombre": "CORTA",
        "correo": "corta@test.com",
        "password": "abc",
        "rol": "empleado",
        "grupo_ids": [],
    })

    assert res.status_code == 422
    assert db_session.query(Empleado).filter_by(correo="corta@test.com").first() is None


def test_crear_usuario_rol_invalido(
    admin_client: tuple[TestClient, Empleado], db_session: Session
) -> None:
    """SPEC-S18-B1 (Failure): rol fuera de la whitelist → 422."""
    client, _ = admin_client

    res = client.post("/coordinacion/usuarios", json={
        "nombre": "MALROL",
        "correo": "malrol@test.com",
        "password": "Relevo2026*",
        "rol": "superadmin",
        "grupo_ids": [],
    })

    assert res.status_code == 422
    assert db_session.query(Empleado).filter_by(correo="malrol@test.com").first() is None


# --- SPEC-S19-A1: whitelist de rol en UsuarioUpdate ---

def test_actualizar_usuario_rol_invalido(
    admin_client: tuple[TestClient, Empleado], db_session: Session
) -> None:
    """SPEC-S19-A1 (Failure): un rol fuera de la whitelist debe rechazarse."""
    client, _ = admin_client
    emp = Empleado(
        nombre="Victima", correo="victima@test.com", password_hash="h", rol="empleado"
    )
    db_session.add(emp)
    db_session.commit()
    emp_id = emp.id

    res = client.patch(f"/coordinacion/usuarios/{emp_id}", json={"rol": "superadmin"})

    assert res.status_code == 422
    db_session.expire_all()
    # El rol original se conserva: nada se persistio
    assert db_session.get(Empleado, emp_id).rol == "empleado"


def test_actualizar_usuario_rol_valido_sin_regresion(
    admin_client: tuple[TestClient, Empleado], db_session: Session
) -> None:
    """SPEC-S19-A1 (Success): un rol de la whitelist sigue funcionando."""
    client, _ = admin_client
    emp = Empleado(
        nombre="Promovido", correo="promo@test.com", password_hash="h", rol="empleado"
    )
    db_session.add(emp)
    db_session.commit()
    emp_id = emp.id

    res = client.patch(f"/coordinacion/usuarios/{emp_id}", json={"rol": "coordinacion"})

    assert res.status_code == 200
    db_session.expire_all()
    assert db_session.get(Empleado, emp_id).rol == "coordinacion"
