"""Tests de idempotencia del seed (SPEC-S18-C1).

El seed corre en CADA arranque del contenedor (`docker-entrypoint.sh`),
por lo que no debe sobrescribir datos que Coordinación haya ajustado
desde el panel.
"""

from collections.abc import Generator

import pytest
from sqlalchemy import StaticPool, create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.database import Base
from app.models import Empleado, Grupo

test_engine = create_engine(
    "sqlite:///:memory:",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)


@pytest.fixture
def db_session(monkeypatch: pytest.MonkeyPatch) -> Generator[Session, None, None]:
    """BD en memoria con el seed apuntando a ella."""
    Base.metadata.create_all(bind=test_engine)

    import app.seed as seed_module

    monkeypatch.setattr(seed_module, "SessionLocal", TestingSessionLocal)
    monkeypatch.setattr(seed_module, "init_db", lambda: None)

    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()
        Base.metadata.drop_all(bind=test_engine)


def test_seed_preserva_grupos_ajustados_por_coordinacion(db_session: Session) -> None:
    """SPEC-S18-C1: un reinicio no debe revertir los grupos de un empleado."""
    from app.seed import seed

    # Primer arranque: crea la nómina base
    seed()

    jorge = db_session.query(Empleado).filter_by(correo="jorge@test.com").first()
    assert jorge is not None
    assert [g.nombre for g in jorge.grupos] == ["G3: Reparto Const. y Penal"]

    # Coordinación reasigna a JORGE desde el panel
    g2 = db_session.query(Grupo).filter_by(nombre="G2: Fichas EJPMS").first()
    assert g2 is not None
    jorge.grupos = [g2]
    db_session.commit()

    # Segundo arranque del contenedor
    seed()

    db_session.expire_all()
    jorge = db_session.query(Empleado).filter_by(correo="jorge@test.com").first()
    assert jorge is not None
    assert [g.nombre for g in jorge.grupos] == ["G2: Fichas EJPMS"], (
        "el seed revirtió una reasignación hecha desde Coordinación"
    )


def test_seed_preserva_min_presentes_ajustado(db_session: Session) -> None:
    """SPEC-S18-C1: un reinicio no debe revertir min_presentes (afecta RN3)."""
    from app.seed import seed

    seed()

    g1 = db_session.query(Grupo).filter_by(nombre="G1: Comunicaciones y Atención").first()
    assert g1 is not None
    assert g1.min_presentes == 2

    # Coordinación ajusta el cupo desde el panel
    g1.min_presentes = 1
    db_session.commit()

    seed()

    db_session.expire_all()
    g1 = db_session.query(Grupo).filter_by(nombre="G1: Comunicaciones y Atención").first()
    assert g1 is not None
    assert g1.min_presentes == 1, "el seed revirtió el min_presentes ajustado (RN3)"


def test_seed_asigna_grupos_en_primera_ejecucion(db_session: Session) -> None:
    """El seed sigue poblando la nómina inicial en una BD vacía."""
    from app.seed import seed

    seed()

    hector = db_session.query(Empleado).filter_by(correo="hector@test.com").first()
    assert hector is not None
    # Multi-grupo: HECTOR pertenece a G1 y G4
    assert sorted(g.nombre for g in hector.grupos) == [
        "G1: Comunicaciones y Atención",
        "G4: Notificaciones y Archivo",
    ]

    brigith = db_session.query(Empleado).filter_by(correo="brigith@test.com").first()
    assert brigith is not None
    assert brigith.grupos == []

    assert db_session.query(Empleado).count() == 14  # 3 coordinadores + 11 empleados


def test_seed_no_duplica_ni_altera_usuarios_nuevos(db_session: Session) -> None:
    """Un usuario creado desde la GUI sobrevive intacto a los reinicios."""
    from app.auth import get_password_hash
    from app.seed import seed

    seed()

    g3 = db_session.query(Grupo).filter_by(nombre="G3: Reparto Const. y Penal").first()
    assert g3 is not None
    nuevo = Empleado(
        nombre="MARIANA",
        correo="mariana@test.com",
        password_hash=get_password_hash("Relevo2026*"),
        rol="empleado",
    )
    nuevo.grupos = [g3]
    db_session.add(nuevo)
    db_session.commit()
    total_antes = db_session.query(Empleado).count()

    seed()

    db_session.expire_all()
    assert db_session.query(Empleado).count() == total_antes
    mariana = db_session.query(Empleado).filter_by(correo="mariana@test.com").first()
    assert mariana is not None
    assert [g.nombre for g in mariana.grupos] == ["G3: Reparto Const. y Penal"]
