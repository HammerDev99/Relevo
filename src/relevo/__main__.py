"""CLI mínimo: lista festivos o genera un .ics para importar al Google Calendar.

Uso:
    python -m relevo listar 2026
    python -m relevo ics 2026 > festivos_2026.ics
"""

from __future__ import annotations

import sys
from datetime import datetime

from relevo.festivos import festivos_de_anio
from relevo.ics_export import exportar_ics
from relevo.result import Failure


def _anio_actual() -> int:
    return datetime.now().year


def main(argv: list[str]) -> int:
    comando = argv[1] if len(argv) > 1 else "listar"
    anio = int(argv[2]) if len(argv) > 2 else _anio_actual()

    if comando == "listar":
        festivos_resultado = festivos_de_anio(anio)
        if isinstance(festivos_resultado, Failure):
            print(f"Error: {festivos_resultado.error}", file=sys.stderr)
            return 1
        for festivo in festivos_resultado.value:
            print(f"{festivo.fecha.isoformat()}  {festivo.nombre}")
        return 0

    if comando == "ics":
        ics_resultado = exportar_ics(anio)
        if isinstance(ics_resultado, Failure):
            print(f"Error: {ics_resultado.error}", file=sys.stderr)
            return 1
        sys.stdout.write(ics_resultado.value)
        return 0

    print(f"Comando desconocido: {comando!r}. Use 'listar' o 'ics'.", file=sys.stderr)
    return 2


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
