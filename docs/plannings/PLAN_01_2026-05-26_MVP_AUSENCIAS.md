# PLAN_01 — MVP Sistema de Gestión de Ausencias "Relevo"

| Campo | Valor |
|-------|-------|
| **Fecha** | 2026-05-26 |
| **Fase CDAID** | Plan |
| **Milestone** | MVP |
| **Autor** | Desarrollo / Dependencia judicial (Colombia) |
| **Objetivo** | Lanzar un MVP funcional, de bajo costo y rápido (<2h) para gestionar vacaciones y permisos de 10 empleados, escalable a una app propia en Python. |

---

## 1. Contexto

Dependencia judicial en Colombia, oficina de 10 empleados organizados en grupos de apoyo cruzado. Se necesita coordinar ausencias (vacaciones y permisos) respetando cupos de concurrencia y privacidad, con miras a escalar a una aplicación propia en Python.

## 2. Reglas de negocio (contrato)

| ID | Regla |
|----|-------|
| RN1 | 10 empleados en grupos de apoyo cruzado. |
| RN2 | 22 días de vacaciones/año y hasta 3 días de permiso/mes por empleado. |
| RN3 | Concurrencia estándar: máximo **1** persona ausente a la vez (cupo estricto). |
| RN4 | Excepción (máximo **2**): solo si una está en vacaciones y otra pide permiso puntual, **o** dos permisos el mismo día por situación concreta y justificada. |
| RN5 | Privacidad: los empleados **no** ven quién pidió ni por qué. Solo ven `DISPONIBLE`, `OCUPADO` o `EXCEPCIONAL`. |
| RN6 | Respaldo: para pedir permiso, el empleado debe haber acordado previamente con un compañero que lo cubrirá. |
| RN7 | Calendario gregoriano + festivos de Colombia (días hábiles reales). |

## 3. Stack del MVP

| Capa | Herramienta | Rol |
|------|-------------|-----|
| Solicitud | Google Forms | Captura de solicitudes (privado para coordinación) |
| Saldos | Google Sheets | Conteo de 22 días/año y 3 días/mes (RN2) |
| Gestión | Trello (privado) | Aprobación/rechazo, árbitro de excepciones (RN4) |
| Visualización | Google Calendar compartido | Bloques de disponibilidad **sin PII** (RN5) |
| Escalado | Script Python (`holidays.CO`) | Cálculo de festivos y días hábiles (RN7) |

---

## ENTREGABLE 1 — Revisión del flujo del MVP: fallas lógicas

El flujo `Forms → Sheet → Trello → Calendar` es **viable**, pero tiene 8 puntos de fricción. Cuatro son condiciones duras (sin ellas el MVP falla en privacidad o en las reglas de concurrencia).

| ID | Falla detectada | Severidad | Mitigación |
|----|-----------------|-----------|------------|
| **F1** | Forms **no valida concurrencia en tiempo real**: el empleado llena el form sin saber si la fecha ya está tomada (Forms no consulta el Calendar). | Alta | El empleado **debe** revisar el Calendar antes (checkbox obligatorio, campo 10). El form es captura, no validación. La coordinación es el árbitro final. |
| **F2** | El **conteo de saldos** (RN2) es manual: ni Forms ni Trello suman días consumidos. Principal fuente de error. | Alta | Google Sheet de saldos (1 fila/empleado). A futuro: el script Python calcula días hábiles exactos. |
| **F3** | La **regla de respaldo (RN6) no se confirma** con el compañero: el solicitante solo declara "X me cubre". | Media | Campo de respaldo + la coordinación verifica con el compañero por canal interno antes de aprobar. No automatizar la confirmación en v1. |
| **F4** | **Riesgo de PII en el Calendar**: si el evento lleva nombre o motivo, rompe RN5. | **Crítica** | Regla dura: los eventos públicos **nunca** llevan nombre ni motivo. Solo título genérico. El detalle vive solo en Sheet/Trello (acceso restringido). |
| **F5** | La **lógica de excepción (RN4) requiere juicio humano**: no se puede automatizar "vacaciones+permiso" o "2 permisos justificados" en Forms/Calendar. | Media | Delegar a coordinación vía Trello. El form permite marcar "solicito como excepción" + justificación; la coordinación decide. |
| **F6** | **Festivos: visual vs cálculo**. Importarlos al Calendar ayuda a verlos, pero contar "22 días hábiles" exige excluir festivos **y** fines de semana (cálculo). | Media | MVP: conteo manual asistido por el calendario. Escala: script Python (Entregable B). |
| **F7** | **Vacaciones y permisos mezclados**: RN2 los trata distinto y la excepción válida (RN4) es justamente "vacaciones+permiso". | Alta | El form **debe** tener campo `Tipo: Vacaciones / Permiso`. Sin esto, RN4 no es evaluable. |
| **F8** | **Condición de carrera**: dos personas piden la misma fecha casi al tiempo, ninguna ve a la otra. | Baja | El timestamp del Form resuelve el orden (FIFO). La coordinación procesa en orden; la 2ª se evalúa como excepción o se rechaza. Aceptable para 10 personas. |

**Condiciones duras (no negociables)**: F1, F4, F7 y el rol de árbitro de coordinación para F5.

**Veredicto**: flujo aprobado con las 4 condiciones duras implementadas.

---

## ENTREGABLE 2 — Estructura de datos del formulario

Campos del Google Form, con visibilidad y regla asociada:

| # | Campo | Tipo | Oblig. | Visibilidad | Regla / Falla |
|---|-------|------|--------|-------------|---------------|
| 1 | Marca temporal | auto | sí | Coordinación | FIFO (F8) |
| 2 | Correo institucional | auto (login) | sí | Coordinación | Notificar resultado |
| 3 | Nombre del solicitante | lista (10) | sí | Coordinación | Identidad — **no pública** (RN5) |
| 4 | Tipo de ausencia | opción `Vacaciones`/`Permiso` | sí | Coordinación | RN2, RN4, RN7 (F7) |
| 5 | Fecha de inicio | fecha | sí | → Calendar (sin nombre) | Rango |
| 6 | Fecha de fin | fecha | sí | → Calendar (sin nombre) | Rango |
| 7 | Días hábiles solicitados | número | sí | Coordinación | Descuenta saldo (F2) |
| 8 | Compañero de respaldo | lista (9, excl. solicitante) | sí | Coordinación | RN6 (F3) |
| 9 | ¿Acordaste el respaldo con tu compañero? | checkbox `Sí, ya acordamos` | sí | Coordinación | RN6 (declaración) |
| 10 | ¿Revisaste disponibilidad en el calendario? | checkbox `Sí` | sí | Coordinación | F1 |
| 11 | ¿Solicitas como excepción de concurrencia? | opción `No`/`Sí` | sí | Coordinación | RN4 (F5) |
| 12 | Justificación (si Permiso o Excepción) | texto largo | condicional | Coordinación — **NUNCA pública** (RN5) | RN4, RN5 |

**Privacidad (RN5)**: los campos 3 y 12 jamás salen del Sheet de respuestas / Trello. El Calendar público solo refleja los campos 5 y 6 traducidos a un **estado derivado**. El respaldo (campo 8) sabe que cubre — es inherente al acuerdo y no viola la privacidad hacia los otros 8.

**Estados derivados visibles en el Calendar** (lo único que ve el empleado):

| Estado | Significado | Personas |
|--------|-------------|----------|
| `DISPONIBLE` | Sin ausencias ese día | 0 |
| `OCUPADO (1/1)` | Cupo estándar lleno (RN3) | 1 |
| `EXCEPCIONAL (2/2)` | Excepción aprobada — tope absoluto (RN4) | 2 |

---

## ENTREGABLE 3 — Gestión de festivos colombianos

**Inmediato (MVP, sin código)** — recomendado para hoy:
- Google Calendar trae festivos oficiales integrados. En el calendar "Ausencias Oficina": **Configuración → Añadir calendario → Examinar calendarios de interés → Días festivos regionales → activar Colombia**. Cero digitación, se actualiza solo cada año.
- **No** buscar archivos `.ics` aleatorios en internet (riesgo de desactualización y de seguridad). El calendario integrado de Google es la fuente confiable.

**Escalable (Python — implementado en Entregable B)**:
- Librería `holidays` (`holidays.CO`). Incluye la **Ley Emiliani** (traslado de festivos al lunes) de forma automática. Verificado: **18 festivos en 2026** (p. ej. Reyes Magos trasladado del 6 ene al 12 ene "observado").
- Permite calcular **días hábiles reales** (excluyendo fines de semana + festivos) → resuelve F2/F6 y el conteo exacto de los 22 días de RN2.

---

## ENTREGABLE 4 — Paso a paso de implementación (<2h)

**Bloque 1 — Calendar (15 min)**
1. Crear calendar "Ausencias Oficina".
2. Activar festivos de Colombia (integrados).
3. Compartir con los 10 empleados en "Ver todos los detalles" (los detalles serán genéricos, sin PII).

**Bloque 2 — Form (40 min)**
4. Crear Google Form con los 12 campos del Entregable 2.
5. Restringir a la organización (login institucional) para capturar el correo.
6. Lógica condicional: mostrar el campo 12 solo si `Tipo=Permiso` o `Excepción=Sí`.
7. Vincular respuestas a una Google Sheet.

**Bloque 3 — Sheet de saldos (20 min)**
8. Pestaña `Saldos`: 10 filas, columnas `Vacaciones_restantes` (inicia en 22) y `Permiso_mes_restante` (inicia en 3).
9. Pestaña `Respuestas` (poblada automáticamente por el Form).

**Bloque 4 — Trello (25 min)**
10. Tablero privado "Coordinación Ausencias" (solo coordinación).
11. Listas: `Solicitudes nuevas → En revisión → Aprobadas → Rechazadas`.
12. Flujo por solicitud: tarjeta → verificar saldo + respaldo + concurrencia → aprobar/rechazar → crear evento **genérico** en Calendar → notificar al solicitante por correo.

**Bloque 5 — Prueba (20 min)**
13. Hacer 2 solicitudes de prueba (una normal, una excepción) y validar el flujo completo y la privacidad (que el Calendar no muestre nombres).

**Total ≈ 2 horas.**

---

## 4. SPECs verificables (alimentan el Sprint — Entregable B)

### SPEC-MVP-B1: Cálculo de festivos colombianos de un año

| Campo | Valor |
|-------|-------|
| **Origen** | Entregable 3 / RN7 |
| **Archivos** | `src/relevo/festivos.py` |
| **Prioridad** | P0 — base de todo cálculo de días hábiles |
| **Estado** | `[x]` completado (2026-05-26) |

**Cambios requeridos**:
1. Función que retorna los festivos colombianos de un año dado (con Ley Emiliani vía `holidays.CO`), envuelta en `Result[T, E]`.
2. Modelo `Festivo` inmutable (`frozen=True`) con fecha y nombre en español.

**Criterios de aceptación**:
- [ ] Retorna 18 festivos para 2026.
- [ ] Incluye festivos trasladados a lunes (Ley Emiliani), p. ej. `2026-01-12` Reyes Magos.
- [ ] Año inválido (p. ej. < 1984, antes de Ley Emiliani moderna, o no-entero) → `Failure`.
- [ ] `pytest -x` pasa sin regresión.

### SPEC-MVP-B2: Cálculo de días hábiles entre dos fechas

| Campo | Valor |
|-------|-------|
| **Origen** | Entregable 3 / F2 / F6 / RN2 |
| **Archivos** | `src/relevo/festivos.py` |
| **Prioridad** | P0 — resuelve el conteo de los 22 días |
| **Estado** | `[x]` completado (2026-05-26) |

**Cambios requeridos**:
1. Función que cuenta días hábiles entre `inicio` y `fin` (inclusive), excluyendo sábados, domingos y festivos colombianos. Envuelta en `Result[T, E]`.

**Criterios de aceptación**:
- [ ] Cuenta correctamente un rango que cruza un fin de semana.
- [ ] Excluye un festivo dentro del rango.
- [ ] `fin < inicio` → `Failure`.
- [ ] Rango de un solo día hábil → 1; de un solo día festivo/fin de semana → 0.
- [ ] `pytest -x` pasa sin regresión.

### SPEC-MVP-B3: Exportación de festivos a archivo `.ics`

| Campo | Valor |
|-------|-------|
| **Origen** | Entregable 3 (importar al Google Calendar) |
| **Archivos** | `src/relevo/ics_export.py` |
| **Prioridad** | P1 — conveniencia para el MVP |
| **Estado** | `[x]` completado (2026-05-26) |

**Cambios requeridos**:
1. Función que genera contenido `.ics` (VCALENDAR) válido con los festivos de un año, como eventos de día completo. Envuelta en `Result[T, E]`.

**Criterios de aceptación**:
- [ ] El contenido empieza con `BEGIN:VCALENDAR` y termina con `END:VCALENDAR`.
- [ ] Contiene un `VEVENT` por festivo.
- [ ] `pytest -x` pasa sin regresión.

---

## 5. Riesgos

| Riesgo | Impacto | Mitigación |
|--------|---------|------------|
| Fuga de PII en el Calendar (F4) | Alto (RN5) | Disciplina de títulos genéricos + revisión en la prueba (Bloque 5). |
| Error en conteo manual de saldos (F2) | Medio | Migrar a cálculo Python (SPEC-B2) en el siguiente sprint. |
| Confirmación de respaldo no verificada (F3) | Medio | Verificación manual por coordinación; automatizar en v2. |
| Festivos desactualizados | Bajo | Usar festivos integrados de Google (auto) + `holidays` actualizado. |

## 6. Decisiones arquitectónicas

- **MVP de no-código primero**: validar el proceso antes de invertir en software propio.
- **Coordinación como árbitro humano** de las reglas que requieren juicio (RN4), en lugar de intentar automatizarlas prematuramente.
- **Separación PII / público**: el dato sensible vive en Sheet/Trello; el Calendar solo expone estados derivados.
- **Python como capa de cálculo** (festivos/días hábiles) desde el día 1, reutilizable cuando se construya la app propia.

## 7. Camino de escalado (VPS de la Rama Judicial)

**Infraestructura disponible**: VPS propio con un dominio **autorizado en la red de la Rama Judicial**. Esto convierte la "app propia futura" en un destino de despliegue **real y autorizado**, no hipotético.

| Etapa | Qué corre | Destino |
|-------|-----------|---------|
| **MVP (hoy)** | Forms + Sheet + Trello + Calendar | Nube Google |
| **v1 (escalado)** | App web Python (p. ej. FastAPI/Flask) que automatiza concurrencia (RN3/RN4), saldos (RN2) y privacidad (RN5) | **VPS + dominio autorizado** |
| **Reutilización** | El módulo `src/relevo/` (festivos + días hábiles) construido hoy es la **capa de cálculo** de esa app v1 — no se descarta. | VPS |

**Implicaciones de diseño para que el código de hoy sirva mañana**:
- Mantener `src/relevo/` **sin acoplamiento** a Google/Trello (lógica de dominio pura) → portable al VPS.
- Al migrar a v1, la app del VPS sustituye el árbitro humano (Trello) por validación automática de RN3/RN4 y persiste PII en BD propia (control total sobre RN5, ventaja frente a tener datos en terceros).
- Considerar para v1: autenticación contra el directorio de la Rama Judicial si el dominio autorizado lo permite (SSO), evitando gestión propia de credenciales.

> **Nota de seguridad**: al estar el dominio en la red de la Rama Judicial, cualquier despliegue v1 debe cumplir las políticas de seguridad de la entidad (manejo de datos personales — Ley 1581 de 2012 de Habeas Data en Colombia, dado que se procesan datos de empleados y motivos de permiso).
