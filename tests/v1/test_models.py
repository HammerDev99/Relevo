from collections.abc import Generator

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.database import Base
from app.models import Empleado, Solicitud

# Test database URL
TEST_DATABASE_URL = "sqlite:///:memory:"


@pytest.fixture
def db_session() -> Generator[Session, None, None]:
    # Use in-memory SQLite for tests
    engine = create_engine(TEST_DATABASE_URL, connect_args={"check_same_thread": False})
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)


def test_create_empleado(db_session: Session) -> None:
    empleado = Empleado(
        nombre="Test User",
        correo="test@ramajudicial.gov.co",
        password_hash="fakehash",
        rol="empleado",
    )
    db_session.add(empleado)
    db_session.commit()

    saved_empleado = db_session.query(Empleado).filter_by(correo="test@ramajudicial.gov.co").first()
    assert saved_empleado is not None
    assert saved_empleado.nombre == "Test User"
    assert saved_empleado.activo is True


def test_create_solicitud(db_session: Session) -> None:
    from datetime import date

    empleado = Empleado(
        nombre="Solicitante", correo="sol@ramajudicial.gov.co", password_hash="fakehash"
    )
    db_session.add(empleado)
    db_session.commit()

    solicitud = Solicitud(
        empleado_id=empleado.id,
        tipo="vacaciones",
        fecha_inicio=date(2026, 6, 1),
        fecha_fin=date(2026, 6, 15),
        dias_habiles=10,
        estado="pendiente",
    )
    db_session.add(solicitud)
    db_session.commit()

    saved_solicitud = db_session.query(Solicitud).first()
    assert saved_solicitud is not None
    assert saved_solicitud.empleado.nombre == "Solicitante"
    assert saved_solicitud.dias_habiles == 10
