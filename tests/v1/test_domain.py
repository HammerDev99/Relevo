from collections.abc import Generator
from datetime import date

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.database import Base
from app.domain import validar_solicitud
from app.models import Empleado, Grupo, Solicitud
from relevo.result import Failure, Success


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


def test_validar_solicitud_vacaciones_excede_saldo(db_session: Session) -> None:
    g = Grupo(nombre="G", min_presentes=0)
    emp1 = Empleado(nombre="Emp1", correo="emp1@test.com", password_hash="h", activo=True)
    resp = Empleado(nombre="Resp", correo="resp@test.com", password_hash="h", activo=True)
    emp1.grupos.append(g)
    resp.grupos.append(g)
    db_session.add_all([g, emp1, resp])
    db_session.commit()

    # Ya tiene 20 días aprobados
    s1 = Solicitud(
        empleado_id=emp1.id,
        tipo="vacaciones",
        fecha_inicio=date(2026, 1, 1),
        fecha_fin=date(2026, 1, 20),
        dias_habiles=20,
        estado="aprobada",
    )
    db_session.add(s1)
    db_session.commit()

    # Intenta pedir 5 días más
    nueva = Solicitud(
        empleado_id=emp1.id,
        tipo="vacaciones",
        fecha_inicio=date(2026, 2, 1),
        fecha_fin=date(2026, 2, 5),
        dias_habiles=5,
        respaldo_id=resp.id,
    )

    result = validar_solicitud(db_session, nueva)
    assert isinstance(result, Failure)
    assert "Saldo vacaciones insuficiente" in result.error


def test_validar_solicitud_permiso_excede_mes(db_session: Session) -> None:
    g = Grupo(nombre="G", min_presentes=0)
    emp1 = Empleado(nombre="Emp1", correo="emp1@test.com", password_hash="h", activo=True)
    resp = Empleado(nombre="Resp", correo="resp@test.com", password_hash="h", activo=True)
    emp1.grupos.append(g)
    resp.grupos.append(g)
    db_session.add_all([g, emp1, resp])
    db_session.commit()

    # Ya tiene 2 días de permiso en Junio
    s1 = Solicitud(
        empleado_id=emp1.id,
        tipo="permiso",
        fecha_inicio=date(2026, 6, 1),
        fecha_fin=date(2026, 6, 2),
        dias_habiles=2,
        estado="aprobada",
    )
    db_session.add(s1)
    db_session.commit()

    # Intenta pedir 2 días más en el mismo mes
    nueva = Solicitud(
        empleado_id=emp1.id,
        tipo="permiso",
        fecha_inicio=date(2026, 6, 10),
        fecha_fin=date(2026, 6, 11),
        dias_habiles=2,
        respaldo_id=resp.id,
    )

    result = validar_solicitud(db_session, nueva)
    assert isinstance(result, Failure)
    assert "Saldo permiso insuficiente para el mes" in result.error


def test_validar_concurrencia_estandar_violada(db_session: Session) -> None:
    g = Grupo(nombre="G", min_presentes=2)  # 3 members, min 2 -> cupo 1
    emp1 = Empleado(nombre="Emp1", correo="emp1@test.com", password_hash="h", activo=True)
    emp2 = Empleado(nombre="Emp2", correo="emp2@test.com", password_hash="h", activo=True)
    resp = Empleado(nombre="Resp", correo="resp@test.com", password_hash="h", activo=True)
    emp1.grupos.append(g)
    emp2.grupos.append(g)
    resp.grupos.append(g)
    db_session.add_all([g, emp1, emp2, resp])
    db_session.commit()

    # Emp1 ya tiene vacaciones aprobadas
    s1 = Solicitud(
        empleado_id=emp1.id,
        tipo="vacaciones",
        fecha_inicio=date(2026, 7, 1),
        fecha_fin=date(2026, 7, 10),
        dias_habiles=8,
        estado="aprobada",
    )
    db_session.add(s1)
    db_session.commit()

    # Emp2 intenta pedir vacaciones que traslapan
    nueva = Solicitud(
        empleado_id=emp2.id,
        tipo="vacaciones",
        fecha_inicio=date(2026, 7, 5),
        fecha_fin=date(2026, 7, 15),
        dias_habiles=7,
        respaldo_id=resp.id,
    )

    result = validar_solicitud(db_session, nueva)
    assert isinstance(result, Failure)
    assert "CUPO_LLENO" in result.error


def test_validar_excepcion_valida(db_session: Session) -> None:
    g = Grupo(nombre="G", min_presentes=1)
    emp1 = Empleado(nombre="Emp1", correo="emp1@test.com", password_hash="h", activo=True)
    emp2 = Empleado(nombre="Emp2", correo="emp2@test.com", password_hash="h", activo=True)
    resp = Empleado(nombre="Resp", correo="resp@test.com", password_hash="h", activo=True)
    emp1.grupos.append(g)
    emp2.grupos.append(g)
    resp.grupos.append(g)
    db_session.add_all([g, emp1, emp2, resp])
    db_session.commit()

    # Emp1 tiene vacaciones
    s1 = Solicitud(
        empleado_id=emp1.id,
        tipo="vacaciones",
        fecha_inicio=date(2026, 7, 1),
        fecha_fin=date(2026, 7, 10),
        dias_habiles=8,
        estado="aprobada",
    )
    db_session.add(s1)
    db_session.commit()

    # Emp2 pide permiso como excepción
    nueva = Solicitud(
        empleado_id=emp2.id,
        tipo="permiso",
        fecha_inicio=date(2026, 7, 5),
        fecha_fin=date(2026, 7, 6),
        dias_habiles=2,
        es_excepcion=True,
        justificacion="Cita médica",
        respaldo_id=resp.id,
    )

    result = validar_solicitud(db_session, nueva)
    assert isinstance(result, Success)


def test_validar_respaldo_obligatorio(db_session: Session) -> None:
    g = Grupo(nombre="G", min_presentes=0)
    emp1 = Empleado(nombre="Emp1", correo="emp1@test.com", password_hash="h", activo=True)
    emp1.grupos.append(g)
    db_session.add_all([g, emp1])
    db_session.commit()

    nueva = Solicitud(
        empleado_id=emp1.id,
        tipo="vacaciones",
        fecha_inicio=date(2026, 8, 1),
        fecha_fin=date(2026, 8, 5),
        dias_habiles=3,
        respaldo_id=None,
    )

    result = validar_solicitud(db_session, nueva)
    assert isinstance(result, Failure)
    assert "Debes indicar un compañero de respaldo" in result.error


def test_validar_respaldo_inactivo(db_session: Session) -> None:
    g = Grupo(nombre="G", min_presentes=0)
    emp1 = Empleado(nombre="Emp1", correo="emp1@test.com", password_hash="h", activo=True)
    resp = Empleado(nombre="Resp", correo="resp@test.com", password_hash="h", activo=False)
    emp1.grupos.append(g)
    resp.grupos.append(g)
    db_session.add_all([g, emp1, resp])
    db_session.commit()

    nueva = Solicitud(
        empleado_id=emp1.id,
        tipo="vacaciones",
        fecha_inicio=date(2026, 8, 1),
        fecha_fin=date(2026, 8, 5),
        dias_habiles=3,
        respaldo_id=resp.id,
    )

    result = validar_solicitud(db_session, nueva)
    assert isinstance(result, Failure)
    assert "El compañero de respaldo no está activo" in result.error


def test_validar_permiso_limite_individual(db_session: Session) -> None:
    g = Grupo(nombre="G", min_presentes=0)
    emp1 = Empleado(nombre="Emp1", correo="emp1@test.com", password_hash="h", activo=True)
    resp = Empleado(nombre="Resp", correo="resp@test.com", password_hash="h", activo=True)
    emp1.grupos.append(g)
    resp.grupos.append(g)
    db_session.add_all([g, emp1, resp])
    db_session.commit()

    # Intenta pedir 4 días de permiso (1 de jun a 5 de jun son 5 días hábiles)
    nueva = Solicitud(
        empleado_id=emp1.id,
        tipo="permiso",
        fecha_inicio=date(2026, 6, 1),
        fecha_fin=date(2026, 6, 5),
        respaldo_id=resp.id,
        justificacion="viaje"
    )

    result = validar_solicitud(db_session, nueva)
    assert isinstance(result, Failure)
    assert "no puede superar los 3 días hábiles" in result.error


def test_validar_duplicidad_dias(db_session: Session) -> None:
    g = Grupo(nombre="G", min_presentes=0)
    emp1 = Empleado(nombre="Emp1", correo="emp1@test.com", password_hash="h", activo=True)
    resp = Empleado(nombre="Resp", correo="resp@test.com", password_hash="h", activo=True)
    emp1.grupos.append(g)
    resp.grupos.append(g)
    db_session.add_all([g, emp1, resp])
    db_session.commit()

    # Ya tiene una solicitud aprobada
    s1 = Solicitud(
        empleado_id=emp1.id,
        tipo="vacaciones",
        fecha_inicio=date(2026, 6, 1),
        fecha_fin=date(2026, 6, 10),
        dias_habiles=7,
        estado="aprobada",
    )
    db_session.add(s1)
    db_session.commit()

    # Intenta pedir permiso para el 5 de junio (traslapa)
    nueva = Solicitud(
        empleado_id=emp1.id,
        tipo="permiso",
        fecha_inicio=date(2026, 6, 5),
        fecha_fin=date(2026, 6, 5),
        respaldo_id=resp.id,
        justificacion="cita"
    )

    result = validar_solicitud(db_session, nueva)
    assert isinstance(result, Failure)
    assert "Ya tienes una solicitud" in result.error


def test_validar_empleado_sin_grupo_permitido(db_session: Session) -> None:
    """SPEC-S16-A4: un empleado sin grupo puede solicitar; se omite concurrencia de grupo."""
    emp1 = Empleado(nombre="SinGrupo", correo="sg@test.com", password_hash="h", activo=True)
    resp = Empleado(nombre="Resp", correo="resp@test.com", password_hash="h", activo=True)
    db_session.add_all([emp1, resp])
    db_session.commit()

    # Permiso de 1 día hábil (2026-09-01 es martes), sin grupos asignados
    nueva = Solicitud(
        empleado_id=emp1.id,
        tipo="permiso",
        fecha_inicio=date(2026, 9, 1),
        fecha_fin=date(2026, 9, 1),
        respaldo_id=resp.id,
        justificacion="cita médica",
    )

    result = validar_solicitud(db_session, nueva)
    assert isinstance(result, Success)


def test_validar_vacaciones_permisos_mismo_mes(db_session: Session) -> None:
    """SPEC-S15-C1: Validar que un empleado puede pedir vacaciones y permisos en el mismo mes."""
    g = Grupo(nombre="G", min_presentes=0)
    emp1 = Empleado(nombre="Emp1", correo="emp1@test.com", password_hash="h", activo=True)
    resp = Empleado(nombre="Resp", correo="resp@test.com", password_hash="h", activo=True)
    emp1.grupos.append(g)
    resp.grupos.append(g)
    db_session.add_all([g, emp1, resp])
    db_session.commit()

    # Vacaciones en junio (5 días)
    s1 = Solicitud(
        empleado_id=emp1.id,
        tipo="vacaciones",
        fecha_inicio=date(2026, 6, 1),
        fecha_fin=date(2026, 6, 5),
        dias_habiles=5,
        estado="aprobada",
        respaldo_id=resp.id,
    )
    db_session.add(s1)
    db_session.commit()

    # Permiso en el mismo mes (2 días, no traslapa con vacaciones)
    nueva = Solicitud(
        empleado_id=emp1.id,
        tipo="permiso",
        fecha_inicio=date(2026, 6, 15),
        fecha_fin=date(2026, 6, 16),
        dias_habiles=2,
        respaldo_id=resp.id,
        justificacion="cita médica"
    )

    result = validar_solicitud(db_session, nueva)
    # Debe ser Success porque no hay traslape de fechas y ambos saldos son independientes
    assert isinstance(result, Success)


def test_excepcion_permiso_sin_justificacion_rechazada(db_session: Session) -> None:
    """SPEC-S16-A2: permiso excepcional sin justificación → Failure (RN4)."""
    g = Grupo(nombre="G_A2a", min_presentes=2)  # 3 miembros → cupo_normal=1
    emp1 = Empleado(nombre="E1", correo="e1_a2a@test.com", password_hash="h", activo=True)
    emp2 = Empleado(nombre="E2", correo="e2_a2a@test.com", password_hash="h", activo=True)
    resp = Empleado(nombre="R", correo="r_a2a@test.com", password_hash="h", activo=True)
    emp1.grupos.append(g)
    emp2.grupos.append(g)
    resp.grupos.append(g)
    db_session.add_all([g, emp1, emp2, resp])
    db_session.commit()

    # emp1 ausente (cupo_normal=1 lleno)
    s1 = Solicitud(
        empleado_id=emp1.id,
        tipo="vacaciones",
        fecha_inicio=date(2026, 8, 3),
        fecha_fin=date(2026, 8, 3),
        dias_habiles=1,
        estado="aprobada",
    )
    db_session.add(s1)
    db_session.commit()

    # emp2 intenta excepción sin justificación
    nueva = Solicitud(
        empleado_id=emp2.id,
        tipo="permiso",
        fecha_inicio=date(2026, 8, 3),
        fecha_fin=date(2026, 8, 3),
        es_excepcion=True,
        justificacion=None,
        respaldo_id=resp.id,
    )
    result = validar_solicitud(db_session, nueva)
    assert isinstance(result, Failure)
    assert "justificación" in result.error.lower()


def test_excepcion_vacaciones_rechazada(db_session: Session) -> None:
    """SPEC-S16-A2: vacaciones no pueden solicitarse como excepción (RN4)."""
    g = Grupo(nombre="G_A2b", min_presentes=2)  # 3 miembros → cupo_normal=1
    emp1 = Empleado(nombre="E1", correo="e1_a2b@test.com", password_hash="h", activo=True)
    emp2 = Empleado(nombre="E2", correo="e2_a2b@test.com", password_hash="h", activo=True)
    resp = Empleado(nombre="R", correo="r_a2b@test.com", password_hash="h", activo=True)
    emp1.grupos.append(g)
    emp2.grupos.append(g)
    resp.grupos.append(g)
    db_session.add_all([g, emp1, emp2, resp])
    db_session.commit()

    # emp1 ausente (cupo_normal=1 lleno)
    s1 = Solicitud(
        empleado_id=emp1.id,
        tipo="permiso",
        fecha_inicio=date(2026, 8, 10),
        fecha_fin=date(2026, 8, 10),
        dias_habiles=1,
        estado="aprobada",
    )
    db_session.add(s1)
    db_session.commit()

    # emp2 intenta vacaciones como excepción (no permitido por RN4)
    nueva = Solicitud(
        empleado_id=emp2.id,
        tipo="vacaciones",
        fecha_inicio=date(2026, 8, 10),
        fecha_fin=date(2026, 8, 10),
        dias_habiles=1,
        es_excepcion=True,
        justificacion="viaje",
        respaldo_id=resp.id,
    )
    result = validar_solicitud(db_session, nueva)
    assert isinstance(result, Failure)
    assert "vacaci" in result.error.lower()


def test_excepcion_composicion_permiso_permiso_success(db_session: Session) -> None:
    """SPEC-S16-A2: composición permiso+permiso (ambos justificados) → Success (RN4)."""
    g = Grupo(nombre="G_A2c", min_presentes=2)  # 3 miembros → cupo_normal=1
    emp1 = Empleado(nombre="E1", correo="e1_a2c@test.com", password_hash="h", activo=True)
    emp2 = Empleado(nombre="E2", correo="e2_a2c@test.com", password_hash="h", activo=True)
    resp = Empleado(nombre="R", correo="r_a2c@test.com", password_hash="h", activo=True)
    emp1.grupos.append(g)
    emp2.grupos.append(g)
    resp.grupos.append(g)
    db_session.add_all([g, emp1, emp2, resp])
    db_session.commit()

    # emp1 ausente por permiso (cupo_normal=1 lleno)
    s1 = Solicitud(
        empleado_id=emp1.id,
        tipo="permiso",
        fecha_inicio=date(2026, 9, 7),
        fecha_fin=date(2026, 9, 7),
        dias_habiles=1,
        estado="aprobada",
        justificacion="cita médica",
    )
    db_session.add(s1)
    db_session.commit()

    # emp2 solicita excepción permiso con justificación → composición permiso+permiso OK
    nueva = Solicitud(
        empleado_id=emp2.id,
        tipo="permiso",
        fecha_inicio=date(2026, 9, 7),
        fecha_fin=date(2026, 9, 7),
        es_excepcion=True,
        justificacion="audiencia judicial",
        respaldo_id=resp.id,
    )
    result = validar_solicitud(db_session, nueva)
    assert isinstance(result, Success)
