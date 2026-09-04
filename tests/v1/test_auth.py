from collections.abc import Generator

import pytest
from fastapi import Depends, FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import StaticPool, create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.auth import (
    get_coordinador,
    get_empleado_actual,
    get_password_hash,
    verify_password,
)
from app.database import Base, get_db
from app.models import Empleado
from app.routes import auth

# Create a test app instance
test_app = FastAPI()
test_app.include_router(auth.router)


@test_app.get("/check-auth")
def check_auth_route(empleado: Empleado = Depends(get_empleado_actual)):
    return {"id": empleado.id, "rol": empleado.rol}


@test_app.get("/check-coordinacion")
def check_coord_route(empleado: Empleado = Depends(get_coordinador)):
    return {"is_admin": True}


# In-memory engine shared by everything in the test process
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

    test_app.dependency_overrides[get_db] = override_get_db

    try:
        yield db
    finally:
        # Clear tables but keep connection for StaticPool
        for table in reversed(Base.metadata.sorted_tables):
            db.execute(table.delete())
        db.commit()
        db.close()
        test_app.dependency_overrides.clear()


@pytest.fixture
def client() -> Generator[TestClient, None, None]:
    return TestClient(test_app)


def test_password_hashing() -> None:
    pwd = "secret-password"
    h = get_password_hash(pwd)
    assert h != pwd
    assert verify_password(pwd, h) is True
    assert verify_password("wrong", h) is False


def test_login_route(db_session: Session, client: TestClient) -> None:
    pwd = "password123"
    h = get_password_hash(pwd)
    emp = Empleado(nombre="Juan", correo="juan@test.com", password_hash=h, rol="empleado")
    db_session.add(emp)
    db_session.commit()

    # Test login
    response = client.post("/login", data={"correo": "juan@test.com", "password": "password123"})
    assert response.status_code == 200
    assert "session" in client.cookies
    assert response.json()["rol"] == "empleado"

    # Test login wrong password
    response = client.post("/login", data={"correo": "juan@test.com", "password": "wrong"})
    assert response.status_code == 401


def test_auth_dependency_with_client(db_session: Session, client: TestClient) -> None:
    pwd = "password123"
    h = get_password_hash(pwd)
    emp = Empleado(nombre="Juan", correo="juan@test.com", password_hash=h, rol="empleado")
    db_session.add(emp)
    db_session.commit()

    # Login to get cookie
    client.post("/login", data={"correo": "juan@test.com", "password": "password123"})

    response = client.get("/check-auth")
    assert response.status_code == 200
    assert response.json()["id"] == emp.id


def test_role_authorization_with_client(db_session: Session, client: TestClient) -> None:
    # Regular employee
    emp_regular = Empleado(
        nombre="Regular",
        correo="reg@test.com",
        password_hash=get_password_hash("h"),
        rol="empleado",
    )
    # Coordinator
    emp_coord = Empleado(
        nombre="Coord",
        correo="coord@test.com",
        password_hash=get_password_hash("h"),
        rol="coordinacion",
    )
    db_session.add_all([emp_regular, emp_coord])
    db_session.commit()

    # Regular tries to access coordination
    client.post("/login", data={"correo": "reg@test.com", "password": "h"})
    response = client.get("/check-coordinacion")
    assert response.status_code == 403

    # Coordinator accesses coordination
    client.post("/login", data={"correo": "coord@test.com", "password": "h"})
    response = client.get("/check-coordinacion")
    assert response.status_code == 200
    assert response.json()["is_admin"] is True


def test_logout(client: TestClient) -> None:
    client.cookies.set("session", "some-token")
    response = client.get("/logout")
    assert response.status_code == 200
    # Check that the Set-Cookie header is present and expires the session
    set_cookie = response.headers.get("set-cookie")
    assert "session=;" in set_cookie or 'session=""' in set_cookie or "Max-Age=0" in set_cookie


def test_cambiar_password_exitoso(db_session: Session, client: TestClient) -> None:
    """SPEC-S14-C4: Test cambio de contraseña exitoso."""
    old_pwd = "password123"
    new_pwd = "newpassword456"
    h = get_password_hash(old_pwd)
    emp = Empleado(nombre="Juan", correo="juan@test.com", password_hash=h, rol="empleado")
    db_session.add(emp)
    db_session.commit()

    # Login
    client.post("/login", data={"correo": "juan@test.com", "password": old_pwd})

    # Cambiar contraseña
    response = client.patch(
        "/usuarios/me/password",
        json={"current_password": old_pwd, "new_password": new_pwd}
    )
    assert response.status_code == 200
    assert response.json()["message"] == "Contraseña actualizada exitosamente"

    # Verificar que la contraseña cambió en DB
    db_session.refresh(emp)
    assert verify_password(new_pwd, emp.password_hash) is True
    assert verify_password(old_pwd, emp.password_hash) is False


def test_pwd_invalid(db_session: Session, client: TestClient) -> None:
    """SPEC-S14-C4: Test cambio de contraseña con actual incorrecta."""
    old_pwd = "password123"
    new_pwd = "newpassword456"
    h = get_password_hash(old_pwd)
    emp = Empleado(nombre="Juan", correo="juan@test.com", password_hash=h, rol="empleado")
    db_session.add(emp)
    db_session.commit()

    # Login
    client.post("/login", data={"correo": "juan@test.com", "password": old_pwd})

    # Intentar cambiar con contraseña actual incorrecta
    response = client.patch(
        "/usuarios/me/password",
        json={"current_password": "wrongpassword", "new_password": new_pwd}
    )
    assert response.status_code == 400
    assert "La contraseña actual es incorrecta" in response.json()["detail"]


def test_cambiar_password_misma_contrasena(db_session: Session, client: TestClient) -> None:
    """SPEC-S14-C4: Test cambio de contraseña con la misma contraseña."""
    old_pwd = "password123"
    h = get_password_hash(old_pwd)
    emp = Empleado(nombre="Juan", correo="juan@test.com", password_hash=h, rol="empleado")
    db_session.add(emp)
    db_session.commit()

    # Login
    client.post("/login", data={"correo": "juan@test.com", "password": old_pwd})

    # Intentar cambiar con la misma contraseña
    response = client.patch(
        "/usuarios/me/password",
        json={"current_password": old_pwd, "new_password": old_pwd}
    )
    assert response.status_code == 400
    assert "La nueva contraseña debe ser diferente a la actual" in response.json()["detail"]


def test_cambiar_password_contrasena_corta(db_session: Session, client: TestClient) -> None:
    """SPEC-S14-C4: Test cambio de contraseña con contraseña muy corta."""
    old_pwd = "password123"
    new_pwd = "1234567"  # 7 caracteres (menos del minimo unificado de 8, AUDIT-H6)
    h = get_password_hash(old_pwd)
    emp = Empleado(nombre="Juan", correo="juan@test.com", password_hash=h, rol="empleado")
    db_session.add(emp)
    db_session.commit()

    # Login
    client.post("/login", data={"correo": "juan@test.com", "password": old_pwd})

    # Intentar cambiar con contraseña muy corta
    response = client.patch(
        "/usuarios/me/password",
        json={"current_password": old_pwd, "new_password": new_pwd}
    )
    assert response.status_code == 400
    assert "al menos 8 caracteres" in response.json()["detail"]
