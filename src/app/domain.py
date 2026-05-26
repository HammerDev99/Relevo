from datetime import timedelta

from sqlalchemy import func, select
from sqlalchemy.orm import Session
from src.app.models import Empleado, Solicitud
from src.relevo.result import Failure, Result, Success

from relevo.festivos import dias_habiles


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

    # Pre-calculo de días hábiles si no vienen
    if not nueva.dias_habiles:
        res_dias = dias_habiles(nueva.fecha_inicio, nueva.fecha_fin)
        if isinstance(res_dias, Failure):
            return Failure(res_dias.error)
        # We can't mutate frozen dataclasses, but Solicitud is a SQLAlchemy model (mutable)
        nueva.dias_habiles = res_dias.value

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

    # 3. Validar Concurrencia (RN3/RN4)
    actual = nueva.fecha_inicio
    while actual <= nueva.fecha_fin:
        ausentes = (
            db.scalars(
                select(Solicitud).where(
                    Solicitud.estado == "aprobada",
                    Solicitud.fecha_inicio <= actual,
                    Solicitud.fecha_fin >= actual,
                    Solicitud.id != nueva.id,
                )
            )
            .all()
        )

        count_ausentes = len(ausentes)

        if not nueva.es_excepcion:
            if count_ausentes >= 1:
                return Failure(f"Cupo lleno para el día {actual.isoformat()}")
        else:
            if count_ausentes >= 2:
                return Failure(f"Cupo máximo alcanzado para el día {actual.isoformat()}")

            if count_ausentes == 1:
                otra = ausentes[0]
                es_valida = False
                if (otra.tipo == "vacaciones" and nueva.tipo == "permiso") or (
                    otra.tipo == "permiso" and nueva.tipo == "vacaciones"
                ) or otra.tipo == "permiso" and nueva.tipo == "permiso":
                    es_valida = True

                if not es_valida:
                    return Failure(
                        f"Excepción no válida para {actual.isoformat()}: "
                        "requiere (vacaciones+permiso) o (2 permisos)"
                    )

        actual += timedelta(days=1)

    return Success(nueva)
