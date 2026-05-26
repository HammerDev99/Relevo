"""Modelos de dominio inmutables. Sin acoplamiento a Google/Trello (portables al VPS)."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date


@dataclass(frozen=True, slots=True)
class Festivo:
    """Día festivo colombiano. Inmutable."""

    fecha: date
    nombre: str

    def to_dict(self) -> dict[str, str]:
        """Serialización JSON-friendly (fecha en ISO 8601)."""
        return {"fecha": self.fecha.isoformat(), "nombre": self.nombre}
