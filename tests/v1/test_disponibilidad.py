from collections.abc import Generator
from datetime import date

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import StaticPool, create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.database import Base, get_db
from app.main import app
from app.models import Empleado, Grupo, Solicitud

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


def test_disponibilidad_sin_pii(client: TestClient, db_session: Session) -> None:
    """SPEC-S18-A1: sin sesion no se exponen nombres (RN5 reformulada en PLAN_09)."""
    # Grupo con 2 miembros, min_presentes=1 → cupo_normal=1, cupo_max=2
    g = Grupo(nombre="G_Enero", min_presentes=1)
    emp1 = Empleado(nombre="Juan PII", correo="juan@test.com", password_hash="h")
    emp2 = Empleado(nombre="Maria PII", correo="maria@test.com", password_hash="h")
    emp1.grupos.append(g)
    emp2.grupos.append(g)
    db_session.add_all([g, emp1, emp2])
    db_session.commit()

    # Juan ausente Jan 1-2
    s1 = Solicitud(
        empleado_id=emp1.id,
        tipo="vacaciones",
        fecha_inicio=date(2026, 1, 1),
        fecha_fin=date(2026, 1, 2),
        dias_habiles=2,
        estado="aprobada",
    )
    # Maria ausente Jan 2-3 (excepcion)
    s2 = Solicitud(
        empleado_id=emp2.id,
        tipo="permiso",
        fecha_inicio=date(2026, 1, 2),
        fecha_fin=date(2026, 1, 3),
        dias_habiles=2,
        estado="aprobada",
        es_excepcion=True,
    )
    db_session.add_all([s1, s2])
    db_session.commit()

    response = client.get("/disponibilidad?anio=2026&mes=1")
    assert response.status_code == 200
    data = response.json()

    # Jan 1: 1 ausente en G >= cupo_normal=1 → OCUPADO
    day1 = next(d for d in data if d["fecha"] == "2026-01-01")
    assert day1["estado"] == "OCUPADO"
    assert day1["vista_general"] is True  # sin sesión → vista general

    # Jan 2: 2 ausentes en G >= cupo_max=2 → EXCEPCIONAL
    day2 = next(d for d in data if d["fecha"] == "2026-01-02")
    assert day2["estado"] == "EXCEPCIONAL"
    assert day2["vista_general"] is True

    # RN5 (PLAN_09): sin sesion los nombres NO se exponen
    str_response = response.text
    assert "Juan" not in str_response
    assert "Maria" not in str_response
    assert "PII" not in str_response
    assert "juan@test.com" not in str_response
    assert all(d["empleados_ausentes"] == [] for d in data)


def test_disponibilidad_por_grupo_con_sesion(client: TestClient, db_session: Session) -> None:
    """SPEC-S16-A1: con sesión el estado es relativo solo a los grupos del usuario."""
    from app.auth import create_session_token

    # G1: grupo del usuario (2 miembros, sin ausentes ese día)
    g1 = Grupo(nombre="G1_Sesion", min_presentes=1)  # cupo_normal=1
    # G2: otro grupo con un ausente (no pertenece al usuario)
    g2 = Grupo(nombre="G2_Sesion", min_presentes=1)  # cupo_normal=1

    emp_usuario = Empleado(
        nombre="Usuario", correo="usuario_ses@test.com", password_hash="h", activo=True
    )
    emp_g1 = Empleado(
        nombre="Comp G1", correo="comp_g1_ses@test.com", password_hash="h", activo=True
    )
    emp_g2a = Empleado(
        nombre="G2 Ausente", correo="g2a_ses@test.com", password_hash="h", activo=True
    )
    emp_g2b = Empleado(
        nombre="G2 Otro", correo="g2b_ses@test.com", password_hash="h", activo=True
    )

    emp_usuario.grupos.append(g1)
    emp_g1.grupos.append(g1)
    emp_g2a.grupos.append(g2)
    emp_g2b.grupos.append(g2)

    db_session.add_all([g1, g2, emp_usuario, emp_g1, emp_g2a, emp_g2b])
    db_session.commit()

    # emp_g2a ausente el 2026-04-06 (lunes) — solo afecta G2
    s1 = Solicitud(
        empleado_id=emp_g2a.id,
        tipo="vacaciones",
        fecha_inicio=date(2026, 4, 6),
        fecha_fin=date(2026, 4, 6),
        dias_habiles=1,
        estado="aprobada",
    )
    db_session.add(s1)
    db_session.commit()

    # Vista sin sesión: evalúa todos los grupos → G2 OCUPADO → día OCUPADO
    response_anonimo = client.get("/disponibilidad?anio=2026&mes=4")
    assert response_anonimo.status_code == 200
    data_anonimo = response_anonimo.json()
    day6_anonimo = next(d for d in data_anonimo if d["fecha"] == "2026-04-06")
    assert day6_anonimo["estado"] == "OCUPADO"
    assert day6_anonimo["vista_general"] is True

    # Vista con sesión de emp_usuario (solo en G1, que no tiene ausentes)
    token = create_session_token({"user_id": emp_usuario.id})
    response_sesion = client.get("/disponibilidad?anio=2026&mes=4", cookies={"session": token})
    assert response_sesion.status_code == 200
    data_sesion = response_sesion.json()
    day6_sesion = next(d for d in data_sesion if d["fecha"] == "2026-04-06")
    # G1 sin ausentes → DISPONIBLE; G2 no se evalúa para este usuario
    assert day6_sesion["estado"] == "DISPONIBLE"
    assert day6_sesion["vista_general"] is False


def test_disponibilidad_parametros_invalidos_422(client: TestClient, db_session: Session) -> None:
    """AUDIT-H1: mes fuera de rango y anio fuera de rango deben retornar 422."""
    assert client.get("/disponibilidad?anio=2026&mes=13").status_code == 422
    assert client.get("/disponibilidad?anio=2026&mes=0").status_code == 422
    assert client.get("/disponibilidad?anio=2019&mes=1").status_code == 422
    assert client.get("/disponibilidad?anio=2101&mes=1").status_code == 422


def test_disponibilidad_nombres_con_sesion(client: TestClient, db_session: Session) -> None:
    """SPEC-S18-A1: con sesion se exponen los nombres de los ausentes."""
    from app.auth import create_session_token

    g = Grupo(nombre="G_Nombres", min_presentes=1)
    emp_ve = Empleado(
        nombre="Observador", correo="obs_nom@test.com", password_hash="h", activo=True
    )
    emp_aus = Empleado(
        nombre="Jorge Ausente", correo="jorge_nom@test.com", password_hash="h", activo=True
    )
    emp_ve.grupos.append(g)
    emp_aus.grupos.append(g)
    db_session.add_all([g, emp_ve, emp_aus])
    db_session.commit()

    db_session.add(Solicitud(
        empleado_id=emp_aus.id,
        tipo="permiso",
        fecha_inicio=date(2026, 5, 4),
        fecha_fin=date(2026, 5, 4),
        dias_habiles=1,
        estado="aprobada",
        justificacion="Cita medica confidencial",
    ))
    db_session.commit()

    token = create_session_token({"user_id": emp_ve.id})
    response = client.get("/disponibilidad?anio=2026&mes=5", cookies={"session": token})
    assert response.status_code == 200
    data = response.json()

    day4 = next(d for d in data if d["fecha"] == "2026-05-04")
    assert day4["empleados_ausentes"] == ["Jorge Ausente"]

    # Un dia sin ausencias no lista a nadie
    day5 = next(d for d in data if d["fecha"] == "2026-05-05")
    assert day5["empleados_ausentes"] == []


def test_disponibilidad_nunca_expone_justificacion(
    client: TestClient, db_session: Session
) -> None:
    """SPEC-S18-A1: la justificacion y el tipo siguen protegidos aun con sesion."""
    from app.auth import create_session_token

    g = Grupo(nombre="G_Justif", min_presentes=1)
    emp_ve = Empleado(
        nombre="MirON", correo="obs_jus@test.com", password_hash="h", activo=True
    )
    emp_aus = Empleado(
        nombre="Ausente Jus", correo="aus_jus@test.com", password_hash="h", activo=True
    )
    emp_ve.grupos.append(g)
    emp_aus.grupos.append(g)
    db_session.add_all([g, emp_ve, emp_aus])
    db_session.commit()

    db_session.add(Solicitud(
        empleado_id=emp_aus.id,
        tipo="permiso",
        fecha_inicio=date(2026, 5, 4),
        fecha_fin=date(2026, 5, 4),
        dias_habiles=1,
        estado="aprobada",
        justificacion="DIAGNOSTICO RESERVADO",
    ))
    db_session.commit()

    token = create_session_token({"user_id": emp_ve.id})
    response = client.get("/disponibilidad?anio=2026&mes=5", cookies={"session": token})

    assert response.status_code == 200
    assert "DIAGNOSTICO RESERVADO" not in response.text
    assert "permiso" not in response.text
