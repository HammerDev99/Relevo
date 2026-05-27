from datetime import date

import pytest
from sqlalchemy.orm import Session

from app.domain import validar_solicitud
from app.models import Empleado, Grupo, Solicitud


@pytest.fixture
def db_session_v3():
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker

    from app.database import Base

    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()

    # Setup group
    grupo = Grupo(nombre="G1", min_presentes=1)
    db.add(grupo)
    db.commit()

    try:
        yield db
    finally:
        db.close()


def test_vacaciones_cuentan_dias_calendario(db_session_v3: Session) -> None:
    """
    S13-C2: Vacaciones proyectan días calendario (incluyendo festivos/findes).
    Lunes 2026-06-01 a Domingo 2026-06-07 son 7 días calendario.
    (Hábiles serían 5).
    """
    grupo = db_session_v3.query(Grupo).first()
    emp = Empleado(nombre="Test", correo="t@r.co", password_hash="h")
    resp = Empleado(nombre="Resp", correo="r@r.co", password_hash="h")
    assert emp is not None
    emp.grupos.append(grupo)
    resp.grupos.append(grupo)
    db_session_v3.add_all([emp, resp])
    db_session_v3.commit()

    sol = Solicitud(
        empleado_id=emp.id,
        tipo="vacaciones",
        fecha_inicio=date(2026, 6, 1),
        fecha_fin=date(2026, 6, 7),
        respaldo_id=resp.id,
    )

    result = validar_solicitud(db_session_v3, sol)
    assert result.is_success
    # Debería haber calculado 7 días, no 5.
    assert sol.dias_habiles == 7


def test_permisos_siguen_contando_dias_habiles(db_session_v3: Session) -> None:
    """
    S13-C2: Permisos siguen permitiendo fraccionamiento (días hábiles).
    Lunes 2026-06-01 a Miércoles 2026-06-03 son 3 días hábiles.
    """
    grupo = db_session_v3.query(Grupo).first()
    emp = Empleado(nombre="Test2", correo="t2@r.co", password_hash="h")
    resp = Empleado(nombre="Resp2", correo="r2@r.co", password_hash="h")
    assert emp is not None
    emp.grupos.append(grupo)
    resp.grupos.append(grupo)
    db_session_v3.add_all([emp, resp])
    db_session_v3.commit()

    sol = Solicitud(
        empleado_id=emp.id,
        tipo="permiso",
        fecha_inicio=date(2026, 6, 1),
        fecha_fin=date(2026, 6, 3),
        respaldo_id=resp.id,
    )

    result = validar_solicitud(db_session_v3, sol)
    assert result.is_success
    assert sol.dias_habiles == 3
