import pytest
from fastapi import FastAPI, Depends
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from src.app.auth import get_password_hash, verify_password, create_session_token, get_empleado_actual, get_coordinador
from src.app.models import Empleado
from src.app.database import Base, get_db
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Mock app for testing dependencies
app = FastAPI()

@app.get("/test-auth")
def test_auth_route(empleado: Empleado = Depends(get_empleado_actual)):
    return {"id": empleado.id, "rol": empleado.rol}

@app.get("/test-coordinacion")
def test_coord_route(empleado: Empleado = Depends(get_coordinador)):
    return {"is_admin": True}

@pytest.fixture
def db_session():
    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    
    # Override get_db dependency
    def override_get_db():
        try:
            yield db
        finally:
            pass
    app.dependency_overrides[get_db] = override_get_db
    
    try:
        yield db
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)
        app.dependency_overrides.clear()

@pytest.fixture
def client():
    return TestClient(app)

def test_password_hashing():
    pwd = "secret-password"
    h = get_password_hash(pwd)
    assert h != pwd
    assert verify_password(pwd, h) is True
    assert verify_password("wrong", h) is False

def test_login_and_auth_dependency(db_session: Session, client: TestClient):
    pwd = "password123"
    h = get_password_hash(pwd)
    emp = Empleado(
        nombre="Juan", 
        correo="juan@test.com", 
        password_hash=h, 
        rol="empleado"
    )
    db_session.add(emp)
    db_session.commit()

    # Manual token creation for testing dependency
    token = create_session_token({"user_id": emp.id, "rol": emp.rol})
    
    # Test with valid cookie
    client.cookies.set("session", token)
    response = client.get("/test-auth")
    assert response.status_code == 200
    assert response.json()["id"] == emp.id

    # Test with invalid cookie
    client.cookies.set("session", "invalid-token")
    response = client.get("/test-auth")
    assert response.status_code == 401

def test_role_authorization(db_session: Session, client: TestClient):
    # Regular employee
    emp_regular = Empleado(
        nombre="Regular", 
        correo="reg@test.com", 
        password_hash=get_password_hash("h"), 
        rol="empleado"
    )
    # Coordinator
    emp_coord = Empleado(
        nombre="Coord", 
        correo="coord@test.com", 
        password_hash=get_password_hash("h"), 
        rol="coordinacion"
    )
    db_session.add_all([emp_regular, emp_coord])
    db_session.commit()

    # Regular tries to access coordination
    token_reg = create_session_token({"user_id": emp_regular.id, "rol": emp_regular.rol})
    client.cookies.set("session", token_reg)
    response = client.get("/test-coordinacion")
    assert response.status_code == 403

    # Coordinator accesses coordination
    token_coord = create_session_token({"user_id": emp_coord.id, "rol": emp_coord.rol})
    client.cookies.set("session", token_coord)
    response = client.get("/test-coordinacion")
    assert response.status_code == 200
    assert response.json()["is_admin"] is True
