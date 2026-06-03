import calendar
from datetime import date

from fastapi import APIRouter, Depends, Query, Request
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.auth import get_session_data
from app.database import get_db
from app.models import Empleado, Grupo, Solicitud
from app.schemas.disponibilidad import DisponibilidadRead
from relevo.festivos import es_festivo

router = APIRouter(prefix="/disponibilidad", tags=["disponibilidad"])


def _empleado_de_sesion(request: Request, db: Session) -> Empleado | None:
    """Retorna el empleado autenticado desde la cookie, o None sin levantar excepción."""
    token = request.cookies.get("session")
    if not token:
        return None
    data = get_session_data(token)
    if not data or "user_id" not in data:
        return None
    empleado = db.get(Empleado, data["user_id"])
    if not empleado or not empleado.activo:
        return None
    return empleado


def _estado_para_grupos(
    grupos: list[Grupo],
    ausentes_dia: list[Solicitud],
) -> str:
    """Retorna el estado más restrictivo entre todos los grupos evaluados."""
    if not grupos:
        return "DISPONIBLE"

    estado = "DISPONIBLE"
    for grupo in grupos:
        miembros_ids = {m.id for m in grupo.miembros if m.activo}
        total = len(miembros_ids)
        cupo_normal = max(0, total - grupo.min_presentes)
        cupo_max = cupo_normal + 1

        count = sum(1 for s in ausentes_dia if s.empleado_id in miembros_ids)

        if count >= cupo_max:
            return "EXCEPCIONAL"  # ya no puede empeorar
        if cupo_normal > 0 and count >= cupo_normal:
            estado = "OCUPADO"

    return estado


@router.get("", response_model=list[DisponibilidadRead])
def consultar_disponibilidad(
    request: Request,
    anio: int = Query(..., ge=2020, le=2100),
    mes: int = Query(..., ge=1, le=12),
    db: Session = Depends(get_db),
) -> list[DisponibilidadRead]:
    """
    Retorna disponibilidad diaria sin PII (RN5).

    Opción A (SPEC-S16-A1):
    - Con sesión + grupos: estado relativo a los grupos del usuario.
    - Sin sesión o sin grupos: vista general informativa (todos los grupos).
    """
    num_dias = calendar.monthrange(anio, mes)[1]
    fecha_inicio_mes = date(anio, mes, 1)
    fecha_fin_mes = date(anio, mes, num_dias)

    # Solicitudes aprobadas que cruzan el mes (con grupos del empleado para tooltip)
    solicitudes = db.scalars(
        select(Solicitud)
        .options(selectinload(Solicitud.empleado).selectinload(Empleado.grupos))
        .where(
            Solicitud.estado == "aprobada",
            Solicitud.fecha_inicio <= fecha_fin_mes,
            Solicitud.fecha_fin >= fecha_inicio_mes,
        )
    ).all()

    # Determinar grupos a evaluar y modo de vista
    empleado = _empleado_de_sesion(request, db)
    vista_general: bool

    if empleado and empleado.grupos:
        grupos_ids = [g.id for g in empleado.grupos]
        grupos_evaluar = list(
            db.scalars(
                select(Grupo)
                .options(selectinload(Grupo.miembros))
                .where(Grupo.id.in_(grupos_ids))
            ).all()
        )
        vista_general = False
    else:
        # Sin sesión o usuario sin grupos: evalúa todos los grupos
        grupos_evaluar = list(
            db.scalars(select(Grupo).options(selectinload(Grupo.miembros))).all()
        )
        vista_general = True

    resultado: list[DisponibilidadRead] = []

    for dia in range(1, num_dias + 1):
        actual = date(anio, mes, dia)
        ausentes_dia = [s for s in solicitudes if s.fecha_inicio <= actual <= s.fecha_fin]

        razon = None
        if es_festivo(actual):
            razon = "Festivo"
        elif actual.weekday() >= 5:
            razon = "Fin de semana"

        estado = _estado_para_grupos(grupos_evaluar, ausentes_dia)

        # Grupos ausentes para tooltip (SPEC-S15-C5): sin PII
        grupos_ausentes: list[str] = []
        for s in ausentes_dia:
            for g in s.empleado.grupos:
                if g.nombre not in grupos_ausentes:
                    grupos_ausentes.append(g.nombre)

        resultado.append(DisponibilidadRead(
            fecha=actual,
            estado=estado,
            razon=razon,
            grupos_ausentes=grupos_ausentes,
            vista_general=vista_general,
        ))

    return resultado
