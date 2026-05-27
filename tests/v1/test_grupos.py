from collections.abc import Generator
from datetime import date

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.database import Base
from app.domain import validar_solicitud
from app.models import Empleado, Grupo, Solicitud


@pytest.fixture
def db_session() -> Generator[Session, None, None]:
    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)


def test_hector_pertenece_a_dos_grupos(db_session: Session) -> None:
    """Verifica que un empleado puede pertenecer a múltiples grupos (M:N)."""
    # G1: Comunicaciones y Atención
    g1 = Grupo(nombre="Comunicaciones y Atención", min_presentes=2)
    # G4: Notificaciones y Archivo
    g4 = Grupo(nombre="Notificaciones y Archivo", min_presentes=1)

    db_session.add_all([g1, g4])
    db_session.commit()

    hector = Empleado(
        nombre="Hector",
        correo="hector@ramajudicial.gov.co",
        password_hash="hash",
    )
    hector.grupos.append(g1)
    hector.grupos.append(g4)

    db_session.add(hector)
    db_session.commit()

    # Recargar y verificar
    hector_db = db_session.get(Empleado, hector.id)
    assert len(hector_db.grupos) == 2
    assert "Comunicaciones y Atención" in [g.nombre for g in hector_db.grupos]
    assert "Notificaciones y Archivo" in [g.nombre for g in hector_db.grupos]


def test_validar_solicitud_por_grupo(db_session: Session) -> None:
    """
    RN3/RN4 evolucionado: La concurrencia se valida por grupo.
    G1 tiene 3 miembros (Nelly, Hector, Flor) y min_presentes=2 (máx 1 ausente).
    """
    g1 = Grupo(nombre="G1", min_presentes=2)
    db_session.add(g1)

    nelly = Empleado(nombre="Nelly", correo="nelly@r.co", password_hash="h")
    hector = Empleado(nombre="Hector", correo="hector@r.co", password_hash="h")
    flor = Empleado(nombre="Flor", correo="flor@r.co", password_hash="h")

    for e in [nelly, hector, flor]:
        assert e is not None
        e.grupos.append(g1)
        db_session.add(e)

    db_session.commit()

    # Nelly pide vacaciones (aprobada)
    sol_nelly = Solicitud(
        empleado_id=nelly.id,
        tipo="vacaciones",
        fecha_inicio=date(2026, 6, 1),
        fecha_fin=date(2026, 6, 5),
        dias_habiles=5,
        respaldo_id=hector.id,
        estado="aprobada",
    )
    db_session.add(sol_nelly)
    db_session.commit()

    # Hector pide permiso en la misma fecha
    sol_hector = Solicitud(
        empleado_id=hector.id,
        tipo="permiso",
        fecha_inicio=date(2026, 6, 1),
        fecha_fin=date(2026, 6, 1),
        dias_habiles=1,
        respaldo_id=flor.id,
    )

    # Debería fallar porque G1 solo permite 1 ausente (3 miembros - 2 min_presentes = 1 cupo)
    result = validar_solicitud(db_session, sol_hector)
    assert not result.is_success
    assert "CUPO_LLENO" in result.error


def test_hector_afecta_multiples_grupos(db_session: Session) -> None:
    """Verifica que la ausencia de Héctor impacta en todos sus grupos."""
    # G1: 2 miembros (Hector, Flor), min_presentes=1 -> 1 cupo
    g1 = Grupo(nombre="G1", min_presentes=1)
    # G4: 2 miembros (Fabian, Hector), min_presentes=1 -> 1 cupo
    g4 = Grupo(nombre="G4", min_presentes=1)
    db_session.add_all([g1, g4])

    hector = Empleado(nombre="Hector", correo="h@r.co", password_hash="h")
    flor = Empleado(nombre="Flor", correo="flor@r.co", password_hash="h")
    fabian = Empleado(nombre="Fabian", correo="fabian@r.co", password_hash="h")

    hector.grupos.extend([g1, g4])
    flor.grupos.append(g1)
    fabian.grupos.append(g4)

    db_session.add_all([hector, flor, fabian])
    db_session.commit()

    # Fabian (G4) ya tiene permiso aprobado
    sol_fabian = Solicitud(
        empleado_id=fabian.id,
        tipo="permiso",
        fecha_inicio=date(2026, 6, 1),
        fecha_fin=date(2026, 6, 1),
        dias_habiles=1,
        respaldo_id=hector.id,
        estado="aprobada",
    )
    db_session.add(sol_fabian)
    db_session.commit()

    # Hector pide permiso. G1 tiene cupo (está solo Flor), pero G4 está lleno (está Fabian)
    sol_hector = Solicitud(
        empleado_id=hector.id,
        tipo="permiso",
        fecha_inicio=date(2026, 6, 1),
        fecha_fin=date(2026, 6, 1),
        dias_habiles=1,
        respaldo_id=flor.id,
    )

    result = validar_solicitud(db_session, sol_hector)
    assert not result.is_success
    assert "CUPO_LLENO" in result.error
