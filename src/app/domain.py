from datetime import timedelta

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models import Empleado, Solicitud
from relevo.festivos import dias_habiles
from relevo.result import Failure, Result, Success


def validar_solicitud(db: Session, nueva: Solicitud) -> Result[Solicitud, str]:
    """Valida una solicitud contra las reglas de negocio (RN2, RN3, RN4, RN6)."""

    # 1. Validar Respaldo (RN6)
    if nueva.respaldo_id is None:
        return Failure("Debes indicar un compañero de respaldo")
    if nueva.respaldo_id == nueva.empleado_id:
        return Failure("No puedes ser tu propio respaldo")

    respaldo = db.get(Empleado, nueva.respaldo_id)
    if not respaldo or not respaldo.activo:
        return Failure("El compañero de respaldo no está activo")

    # S14-C2: Req 4 - Duplicidad de días
    # Verificar si el usuario ya tiene una solicitud que se traslape con este periodo
    query_superposicion = select(func.count(Solicitud.id)).where(
        Solicitud.empleado_id == nueva.empleado_id,
        Solicitud.estado.in_(["aprobada", "pendiente"]),
        Solicitud.fecha_inicio <= nueva.fecha_fin,
        Solicitud.fecha_fin >= nueva.fecha_inicio
    )
    if nueva.id:
        query_superposicion = query_superposicion.where(Solicitud.id != nueva.id)
        
    superposicion = db.scalar(query_superposicion) or 0
    if superposicion > 0:
        return Failure("Ya tienes una solicitud en curso para ese mismo periodo")

    # Pre-calculo de días según tipo (S13-C2)
    if not nueva.dias_habiles:
        if nueva.tipo == "vacaciones":
            # Días calendario (sin saltar festivos)
            conteo = (nueva.fecha_fin - nueva.fecha_inicio).days + 1
            nueva.dias_habiles = conteo
        else:
            # Días hábiles para permisos
            res_dias = dias_habiles(nueva.fecha_inicio, nueva.fecha_fin)
            if isinstance(res_dias, Failure):
                return Failure(res_dias.error)
            nueva.dias_habiles = res_dias.value
            
            # S14-C2: Req 7 - Límite individual de 3 días para permisos
            if nueva.dias_habiles > 3:
                return Failure(
                    "La duración de un permiso individual no puede superar los 3 días hábiles"
                )

    # 2. Validar Saldo (RN2)
    if nueva.tipo == "vacaciones":
        anio = nueva.fecha_inicio.year
        usado_vacaciones = db.scalar(
            select(func.sum(Solicitud.dias_habiles)).where(
                Solicitud.empleado_id == nueva.empleado_id,
                Solicitud.tipo == "vacaciones",
                Solicitud.estado == "aprobada",
                func.strftime("%Y", Solicitud.fecha_inicio) == str(anio),
            )
        ) or 0

        if usado_vacaciones + nueva.dias_habiles > 22:
            return Failure(
                f"Saldo vacaciones insuficiente. Usado: {usado_vacaciones}, "
                f"Pedido: {nueva.dias_habiles}"
            )

    elif nueva.tipo == "permiso":
        anio_mes = nueva.fecha_inicio.strftime("%Y-%m")
        usado_permiso = db.scalar(
            select(func.sum(Solicitud.dias_habiles)).where(
                Solicitud.empleado_id == nueva.empleado_id,
                Solicitud.tipo == "permiso",
                Solicitud.estado == "aprobada",
                func.strftime("%Y-%m", Solicitud.fecha_inicio) == anio_mes,
            )
        ) or 0

        if usado_permiso + nueva.dias_habiles > 3:
            return Failure(
                f"Saldo permiso insuficiente para el mes. Usado: {usado_permiso}, "
                f"Pedido: {nueva.dias_habiles}"
            )

    # 3. Validar Concurrencia por Grupo (S13-C1)
    empleado = db.get(Empleado, nueva.empleado_id)
    if not empleado:
        return Failure("Empleado no encontrado")

    # Empleado sin grupo (SPEC-S16-A4, decisión 2026-06-02): puede solicitar
    # aplicando solo saldos (RN2), respaldo (RN6) y duplicidad. No se evalúa
    # concurrencia de grupo (el bucle se omite al no tener grupos).
    for grupo in empleado.grupos:
        # N = total miembros activos del grupo
        miembros_ids = [m.id for m in grupo.miembros if m.activo]
        total_miembros = len(miembros_ids)
        # Cupo es la cantidad máxima de ausentes permitidos
        cupo_normal = max(0, total_miembros - grupo.min_presentes)
        cupo_max = cupo_normal + 1 # S13-C3: Una excepción permitida
        
        actual = nueva.fecha_inicio
        while actual <= nueva.fecha_fin:
            # Contar ausentes en este grupo para esta fecha (aprobadas)
            ausentes_count = db.scalar(
                select(func.count(Solicitud.id)).where(
                    Solicitud.estado == "aprobada",
                    Solicitud.fecha_inicio <= actual,
                    Solicitud.fecha_fin >= actual,
                    Solicitud.id != nueva.id,
                    Solicitud.empleado_id.in_(miembros_ids)
                )
            ) or 0
            
            if not nueva.es_excepcion and ausentes_count >= cupo_normal:
                return Failure(
                    f"CUPO_LLENO: El grupo {grupo.nombre} ya tiene {ausentes_count} "
                    f"ausentes el día {actual.isoformat()}. Límite normal: {cupo_normal}."
                )
            
            if nueva.es_excepcion and ausentes_count >= cupo_max:
                return Failure(
                    f"LIMITE_EXCEPCIONAL: El grupo {grupo.nombre} ya alcanzó el máximo de "
                    f"{ausentes_count} ausentes el día {actual.isoformat()} (incluyendo "
                    f"excepciones)."
                )
            
            actual += timedelta(days=1)

    return Success(nueva)
