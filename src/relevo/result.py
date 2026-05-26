"""Patrón Result (Railway Oriented Programming).

Modela éxito/fallo de forma explícita sin usar excepciones para flujo de control.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class Success[T]:
    """Resultado exitoso que envuelve un valor."""

    value: T

    @property
    def is_success(self) -> bool:
        return True


@dataclass(frozen=True, slots=True)
class Failure[E]:
    """Resultado fallido que envuelve un error."""

    error: E

    @property
    def is_success(self) -> bool:
        return False


type Result[T, E] = Success[T] | Failure[E]
