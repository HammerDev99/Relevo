# SPRINT_01 — Capa de cálculo de festivos colombianos

| Campo | Valor |
|-------|-------|
| **Fecha** | 2026-05-26 |
| **Fase CDAID** | Do |
| **Origen** | PLAN_01 (Entregable B) |
| **Objetivo** | Implementar la capa de cálculo (festivos + días hábiles) reutilizable para el MVP y la app v1 del VPS. |

## SPECs entregados

| SPEC | Descripción | Estado | Criterios |
|------|-------------|--------|-----------|
| SPEC-MVP-B1 | Festivos colombianos de un año (Ley Emiliani) | ✅ Done | 18 festivos 2026; traslado a lunes; año inválido → Failure |
| SPEC-MVP-B2 | Días hábiles entre dos fechas | ✅ Done | excluye finde/festivos; multi-año; `fin<inicio` → Failure |
| SPEC-MVP-B3 | Exportación a `.ics` | ✅ Done | VCALENDAR válido; 1 VEVENT/festivo; año inválido → Failure |

## Artefactos

| Archivo | Rol |
|---------|-----|
| `src/relevo/result.py` | Patrón `Result[T,E]` (Success/Failure) |
| `src/relevo/logger.py` | `get_logger` |
| `src/relevo/models.py` | `Festivo` (frozen, `to_dict`) |
| `src/relevo/festivos.py` | `festivos_de_anio`, `dias_habiles` |
| `src/relevo/ics_export.py` | `exportar_ics` |
| `src/relevo/__main__.py` | CLI: `listar` / `ics` |
| `tests/` | 18 tests (Success + Failure) |

## Verificación (Check)

| Herramienta | Resultado |
|-------------|-----------|
| `pytest` | 18 passed |
| `ruff check` | All checks passed |
| `mypy` (strict) | Success: no issues (7 archivos) |

## Decisiones técnicas

- Se usa `holidays.country_holidays("CO", ...)` (API tipada) en vez de `holidays.CO` para satisfacer `mypy --strict`.
- `Result` con PEP 695 (`type Result[T, E] = Success[T] | Failure[E]`), `@dataclass(frozen=True, slots=True)`.
- Validación de año en boundary (rechaza no-entero, bool y `< 1984` — Ley Emiliani vigente desde 1984).
- Logs a `stderr` → `python -m relevo ics 2026 > festivos.ics` produce un `.ics` limpio.

## Uso

```powershell
.venv\Scripts\pip install -e .
.venv\Scripts\python.exe -m relevo listar 2026
.venv\Scripts\python.exe -m relevo ics 2026 > festivos_2026.ics
```

## Pendiente (siguiente Planning)

- Lógica de concurrencia (RN3/RN4) y saldos (RN2) — candidata a la app v1 en el VPS.
- Confirmación automática de respaldo (F3) — diferido a v2.
