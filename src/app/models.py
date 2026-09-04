from datetime import UTC, date, datetime
from typing import Optional

from sqlalchemy import Boolean, Column, Date, DateTime, ForeignKey, Integer, String, Table, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .database import Base
from .roles import ROL_EMPLEADO

# Association table for many-to-many relationship
empleado_grupo = Table(
    "empleado_grupo",
    Base.metadata,
    Column("empleado_id", ForeignKey("empleados.id", ondelete="CASCADE"), primary_key=True),
    Column("grupo_id", ForeignKey("grupos.id", ondelete="CASCADE"), primary_key=True),
)


class Grupo(Base):
    __tablename__ = "grupos"

    id: Mapped[int] = mapped_column(primary_key=True)
    nombre: Mapped[str] = mapped_column(String(100), unique=True)
    min_presentes: Mapped[int] = mapped_column(Integer, default=1)

    # Relationships
    miembros: Mapped[list["Empleado"]] = relationship(
        secondary=empleado_grupo, back_populates="grupos"
    )


class Empleado(Base):
    __tablename__ = "empleados"

    id: Mapped[int] = mapped_column(primary_key=True)
    nombre: Mapped[str] = mapped_column(String(100))
    correo: Mapped[str] = mapped_column(String(200), unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(String(200))
    rol: Mapped[str] = mapped_column(String(20), default=ROL_EMPLEADO)
    activo: Mapped[bool] = mapped_column(Boolean, default=True)
    creado_en: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(UTC))

    # Relationships
    solicitudes: Mapped[list["Solicitud"]] = relationship(
        back_populates="empleado", 
        foreign_keys="Solicitud.empleado_id",
        cascade="all, delete-orphan"
    )
    grupos: Mapped[list["Grupo"]] = relationship(
        secondary=empleado_grupo, back_populates="miembros"
    )

    @property
    def grupo_ids(self) -> list[int]:
        return [g.id for g in self.grupos]


class Solicitud(Base):
    __tablename__ = "solicitudes"

    id: Mapped[int] = mapped_column(primary_key=True)
    empleado_id: Mapped[int] = mapped_column(ForeignKey("empleados.id", ondelete="CASCADE"))
    tipo: Mapped[str] = mapped_column(String(20)) # 'vacaciones' or 'permiso'
    fecha_inicio: Mapped[date] = mapped_column(Date)
    fecha_fin: Mapped[date] = mapped_column(Date)
    dias_habiles: Mapped[int] = mapped_column(Integer)
    respaldo_id: Mapped[int | None] = mapped_column(
        ForeignKey("empleados.id", ondelete="SET NULL"), nullable=True
    )
    # 'pendiente', 'aprobada', 'rechazada'
    estado: Mapped[str] = mapped_column(String(20), default="pendiente") 
    es_excepcion: Mapped[bool] = mapped_column(Boolean, default=False)
    justificacion: Mapped[str | None] = mapped_column(Text, nullable=True)
    creada_en: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(UTC))
    procesada_en: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    procesada_por_id: Mapped[int | None] = mapped_column(
        ForeignKey("empleados.id", ondelete="SET NULL"), nullable=True
    )

    # Relationships
    empleado: Mapped["Empleado"] = relationship(
        back_populates="solicitudes",
        foreign_keys=[empleado_id]
    )
    respaldo: Mapped[Optional["Empleado"]] = relationship(foreign_keys=[respaldo_id])
    procesada_por: Mapped[Optional["Empleado"]] = relationship(foreign_keys=[procesada_por_id])


class ConfiguracionApp(Base):
    """Singleton de configuración global de la aplicación."""
    __tablename__ = "configuracion_app"

    id: Mapped[int] = mapped_column(primary_key=True, default=1)
    mostrar_grupos_tooltip: Mapped[bool] = mapped_column(Boolean, default=True)
