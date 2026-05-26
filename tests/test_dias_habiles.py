"""Tests de SPEC-MVP-B2: cálculo de días hábiles."""

from __future__ import annotations

from datetime import date

from relevo.festivos import dias_habiles
from relevo.result import Failure, Success


def test_cruza_fin_de_semana() -> None:
    # vie 2026-01-02 a lun 2026-01-05: cuentan viernes y lunes (sáb/dom no).
    resultado = dias_habiles(date(2026, 1, 2), date(2026, 1, 5))
    assert isinstance(resultado, Success)
    assert resultado.value == 2


def test_excluye_festivo_en_el_rango() -> None:
    # lun 2026-07-20 (Independencia, festivo) a vie 2026-07-24: 4 hábiles, no 5.
    resultado = dias_habiles(date(2026, 7, 20), date(2026, 7, 24))
    assert isinstance(resultado, Success)
    assert resultado.value == 4


def test_rango_multianio_excluye_festivo() -> None:
    # mié 2025-12-31 a vie 2026-01-02: cuentan miércoles y viernes (jue 01-01 festivo).
    resultado = dias_habiles(date(2025, 12, 31), date(2026, 1, 2))
    assert isinstance(resultado, Success)
    assert resultado.value == 2


def test_fin_antes_de_inicio_falla() -> None:
    resultado = dias_habiles(date(2026, 1, 10), date(2026, 1, 1))
    assert isinstance(resultado, Failure)


def test_un_solo_dia_habil() -> None:
    resultado = dias_habiles(date(2026, 1, 2), date(2026, 1, 2))  # viernes
    assert isinstance(resultado, Success)
    assert resultado.value == 1


def test_un_solo_dia_festivo() -> None:
    resultado = dias_habiles(date(2026, 1, 1), date(2026, 1, 1))  # Año Nuevo
    assert isinstance(resultado, Success)
    assert resultado.value == 0


def test_un_solo_dia_fin_de_semana() -> None:
    resultado = dias_habiles(date(2026, 1, 3), date(2026, 1, 3))  # sábado
    assert isinstance(resultado, Success)
    assert resultado.value == 0
