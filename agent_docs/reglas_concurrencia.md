# Reglas de Concurrencia por Grupo — Relevo

> Referencia del modelo de cupos (v3). Autoritativo a partir de PLAN_05.
> Motor: `src/app/domain.py::validar_solicitud`.

---

## 1. Fórmula de cupos

```
cupo_normal = miembros_activos_del_grupo − min_presentes
cupo_max    = cupo_normal + 1                          # una excepción por grupo
```

| Condición | Estado | Acción posible |
|-----------|--------|----------------|
| `ausentes < cupo_normal` | 🟢 DISPONIBLE | Solicitud estándar aprobada |
| `ausentes == cupo_normal` | 🟡 OCUPADO | Solo excepción (RN4) |
| `ausentes >= cupo_max` | 🔴 EXCEPCIONAL | Sin más ausencias posibles en el grupo |

---

## 2. Composición de grupos (seed canónico — v3)

| Grupo | Miembros | `min_presentes` | `cupo_normal` | `cupo_max` |
|-------|----------|:---------------:|:-------------:|:----------:|
| G1: Comunicaciones y Atención | FLOR, NELLY, HECTOR | 2 | 1 | 2 |
| G2: Fichas EJPMS | JACKSON, AMERICA, DANIEL | 2 | 1 | 2 |
| G3: Reparto Const. y Penal | JORGE, YESENIA, DANIELA | 2 | 1 | 2 |
| G4: Notificaciones y Archivo | FABIAN, HECTOR | 1 | 1 | 2 |

> **Multi-grupo**: HECTOR pertenece a G1 y G4. Su ausencia consume cupo en ambos grupos simultáneamente.
> **Sin grupo**: BRIGITH. Puede solicitar (saldos + respaldo), sin restricción de concurrencia.

---

## 3. Excepción (RN4)

La excepción (`cupo_normal + 1`) solo se permite bajo las siguientes condiciones:

1. La solicitud debe ser **permiso** (no vacaciones).
2. La solicitud debe llevar **justificación** no vacía.

Las composiciones permitidas por RN4 (vacaciones+permiso, o 2 permisos justificados) se garantizan implícitamente: la condición 1 excluye vacaciones como excepción, y la condición 2 exige justificación en todos los casos. El conteo del bucle de concurrencia verifica que no se supere `cupo_max`.

> Validado en `domain.py` antes del bucle de concurrencia (`SPEC-S16-A2`).

---

## 4. Ejemplos resueltos

### Caso 1: G3 con 1 ausente (JORGE de vacaciones)
- G3 activos = 3, min_presentes = 2 → cupo_normal = 1
- JORGE ausente → ausentes_G3 = 1 = cupo_normal → **OCUPADO en G3**
- YESENIA solicita estándar → Failure "CUPO_LLENO"
- DANIELA solicita excepción permiso con justificación → ausentes_G3 = 1 < cupo_max (2) → **Success**
- Efecto en G2 y G1: ninguno (JORGE no pertenece a esos grupos)

### Caso 2: HECTOR de vacaciones (multi-grupo)
- HECTOR ausente → consume 1 cupo en G1 y 1 cupo en G4
- G1: ausentes = 1 = cupo_normal(1) → **OCUPADO en G1**
- G4: ausentes = 1 = cupo_normal(1) → **OCUPADO en G4**
- FLOR (G1) solicita estándar → Failure "CUPO_LLENO" (bloqueada por G1)
- FABIAN (G4) solicita excepción permiso con justificación → ausentes_G4 = 1 < cupo_max(2) → **Success**

### Caso 3: BRIGITH (sin grupo)
- Sin grupos asignados → el bucle de concurrencia se omite
- Solo se validan: saldos RN2, respaldo RN6, duplicidad
- Solicitud estándar → **Success** (si saldos disponibles y respaldo válido)

---

## 5. Relación con el calendario

El endpoint `GET /disponibilidad` proyecta el estado de cupos por día:

- **Con sesión**: evalúa solo los grupos del usuario → estado personalizado.
- **Sin sesión**: evalúa todos los grupos → estado más restrictivo (vista general).

El calendario es una **proyección de lectura**; el motor de reglas en `domain.py` es la fuente de verdad al momento de crear solicitudes.

---

## 6. Privacidad de la proyección (RN5)

> Reformulada en **PLAN_09** (2026-09-04). Sustituye la redacción anterior
> ("el dato sensible jamás se expone públicamente").

El endpoint `GET /disponibilidad` **no exige autenticación**, por lo que la
exposición de datos se gradúa según haya o no sesión válida:

| Campo | Sin sesión | Con sesión |
|-------|:----------:|:----------:|
| `estado` (DISPONIBLE/OCUPADO/EXCEPCIONAL) | ✅ | ✅ |
| `razon` (Festivo / Fin de semana) | ✅ | ✅ |
| `grupos_ausentes` (nombres de grupo) | ✅ | ✅ |
| `empleados_ausentes` (nombres de persona) | ❌ vacío | ✅ |
| `tipo` (vacaciones / permiso) | ❌ nunca | ❌ nunca |
| `justificacion` (motivo) | ❌ nunca | ❌ nunca |

**Invariantes verificadas por tests** (`tests/v1/test_disponibilidad.py`):

- `test_disponibilidad_sin_pii` — sin sesión, `empleados_ausentes` está vacío
  y ningún nombre aparece en la respuesta.
- `test_disponibilidad_nombres_con_sesion` — con sesión, los nombres se listan.
- `test_disponibilidad_nunca_expone_justificacion` — ni el motivo ni el tipo
  aparecen en la respuesta, ni siquiera con sesión.

**Motivo de la acotación por sesión**: sin ese condicionante, los nombres
quedarían accesibles a cualquier cliente que alcance la URL dentro de la red
de la Rama Judicial. La justificación del permiso es el dato de mayor
sensibilidad bajo la Ley 1581/2012 y queda fuera del cambio.

**Nota de implementación**: el tooltip del calendario se inyecta con
`unsafe_allow_html`; los nombres se escapan con `html.escape()` en
`gui/pages/02_disponibilidad.py` antes de incorporarse al atributo `title`.
