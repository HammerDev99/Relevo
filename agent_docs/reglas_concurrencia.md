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
3. La composición resultante debe ser: **vacaciones + permiso** o **permiso + permiso** (ambos justificados).

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
