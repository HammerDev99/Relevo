import calendar
from datetime import date

from fastapi import APIRouter, Depends, Query, Request
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.auth import get_empleado_opcional
from app.database import get_db
from app.models import Empleado, Grupo, Solicitud
from app.schemas.disponibilidad import DisponibilidadRead
from relevo.festivos import es_festivo

router = APIRouter(prefix="/disponibilidad", tags=["disponibilidad"])


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
    Retorna la disponibilidad diaria (RN5, reformulada en PLAN_09).

    SPEC-S18-D1: el `estado` evalúa **todos** los grupos, con o sin sesión, de
    modo que el panorama es idéntico para cualquier visitante.

    - Con sesión: se añaden `empleados_ausentes` (nombres) y
      `estado_grupo_propio` (el cupo acotado a los grupos del usuario).
    - Sin sesión: solo estados derivados y nombres de grupo.
    - El tipo de ausencia y la justificación no se exponen nunca.
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

    # SPEC-S18-D1: el estado del día refleja SIEMPRE todos los grupos, con o
    # sin sesión, para que el panorama sea idéntico al de la vista anónima.
    empleado = get_empleado_opcional(request, db)

    grupos_evaluar = list(
        db.scalars(select(Grupo).options(selectinload(Grupo.miembros))).all()
    )

    # Grupos del usuario: permiten avisar si SU cupo sigue libre aunque el día
    # aparezca ocupado por saturación de otro grupo (RN3 se evalúa por grupo).
    grupos_propios = (
        [g for g in grupos_evaluar if g.id in {gr.id for gr in empleado.grupos}]
        if empleado and empleado.grupos
        else []
    )
    vista_general = not grupos_propios

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

        # Grupos ausentes para tooltip (SPEC-S15-C5)
        grupos_ausentes: list[str] = []
        for s in ausentes_dia:
            for g in s.empleado.grupos:
                if g.nombre not in grupos_ausentes:
                    grupos_ausentes.append(g.nombre)

        # Nombres de ausentes (SPEC-S18-A1, RN5 reformulada en PLAN_09).
        # Solo para usuarios autenticados: el endpoint es accesible sin sesión.
        # Nunca se expone el tipo de ausencia ni la justificación.
        empleados_ausentes: list[str] = []
        if empleado:
            for s in ausentes_dia:
                if s.empleado.nombre not in empleados_ausentes:
                    empleados_ausentes.append(s.empleado.nombre)

        # SPEC-S18-D1: reutiliza el mismo cálculo de cupos, acotado a los
        # grupos del usuario. None cuando no hay sesión o no tiene grupos.
        estado_grupo_propio = (
            _estado_para_grupos(grupos_propios, ausentes_dia)
            if grupos_propios
            else None
        )

        resultado.append(DisponibilidadRead(
            fecha=actual,
            estado=estado,
            razon=razon,
            grupos_ausentes=grupos_ausentes,
            vista_general=vista_general,
            empleados_ausentes=empleados_ausentes,
            estado_grupo_propio=estado_grupo_propio,
        ))

    return resultado
