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
