# Relevo — Sistema de Gestión de Ausencias

Sistema diseñado para la coordinación de vacaciones y permisos en dependencias judiciales de Colombia. Este MVP permite gestionar las ausencias de hasta 10 empleados garantizando la continuidad del servicio mediante reglas de concurrencia y protegiendo la privacidad del personal.

## 🚀 Características Principales

- **Cálculo de Festivos Colombianos**: Integración con la Ley Emiliani (Ley 51 de 1983) para determinar días hábiles reales.
- **Validación de Reglas de Negocio**:
  - Saldo de 22 días de vacaciones al año.
  - Saldo de 3 días de permiso al mes.
  - Control de concurrencia (máximo 1 ausente estándar, hasta 2 en excepciones).
  - Validación de compañero de respaldo obligatorio.
- **Privacidad (RN5)**: El calendario nunca expone el motivo ni el tipo de la ausencia. Los nombres de los ausentes se muestran solo a usuarios autenticados; sin sesión la vista es anónima (por grupos).
- **Portal de Coordinación**: Herramientas para que jueces y jefes de despacho aprueben o rechacen solicitudes con visibilidad completa.
- **Arquitectura Profesional**: Backend en FastAPI, Frontend en Streamlit y persistencia en SQLAlchemy 2.0.

## 🛠️ Stack Tecnológico

- **Backend**: Python 3.12, FastAPI, SQLAlchemy 2.0 (Modern Mappings).
- **Frontend**: Streamlit (Modular Services Architecture).
- **Seguridad**: Hashing bcrypt y sesiones firmadas (itsdangerous).
- **Base de Datos**: SQLite (Optimizado para volumen de 10-20 usuarios).
- **Contenerización**: Docker & Docker Compose (Multi-stage builds, gosu para seguridad).

## 🏃 Cómo empezar (Desarrollo Local)

### Requisitos
- Docker y Docker Compose instalados.

### Ejecución
1. Clonar el repositorio.
2. Levantar el ecosistema completo (API + GUI):
   ```bash
   docker-compose -f docker-compose.dev.yml up --build
   ```
3. Acceder a la interfaz: [http://localhost:8501](http://localhost:8501)
4. Documentación de la API: [http://localhost:8000/docs](http://localhost:8000/docs)

## 📂 Estructura del Proyecto

```text
├── src/
│   ├── relevo/         # Motor core de cálculo de festivos
│   └── app/
│       ├── gui/        # Interfaz de usuario (Streamlit)
│       ├── routes/     # Endpoints REST (FastAPI)
│       ├── models.py   # Modelos de base de datos
│       └── domain.py   # Reglas de negocio (Source of Truth)
├── docs/               # Documentación SDD (Plannings, Sprints, Audits)
├── agent_docs/         # Manuales técnicos para agentes IA
└── tests/              # Suite de pruebas integrales
```

## 📋 Reglas de Negocio

### Saldos por empleado

| Tipo | Saldo | Período |
|------|-------|---------|
| Vacaciones | 22 días calendario | Anual |
| Permisos | 3 días hábiles | Mensual (máx. 3 días consecutivos por solicitud) |

Un empleado puede solicitar vacaciones y permisos en el mismo mes sin conflicto — los saldos son independientes.

### Concurrencia por grupo

La regla de concurrencia opera **independientemente por grupo de trabajo**, no de forma global:

| Concepto | Fórmula | Ejemplo (G3: 3 miembros, min 2) |
|---------|---------|--------------------------------|
| `cupo_normal` | `miembros_activos − min_presentes` | `3 − 2 = 1` (1 ausente normal) |
| `cupo_max` | `cupo_normal + 1` | `2` (1 excepción adicional) |
| Estado: Disponible | `ausentes < cupo_normal` | 0 ausentes en G3 |
| Estado: Ocupado | `ausentes == cupo_normal` | 1 ausente en G3 → se requiere excepción (RN4) |
| Estado: Excepcional | `ausentes >= cupo_max` | 2+ ausentes en G3 → no se pueden agregar más |

> **Ejemplo**: si JORGE (G3) está ausente, ese día solo afecta la disponibilidad de G3 — JACKSON (G2) puede ausentarse sin problema si su grupo tiene cupo. Cada grupo gestiona su propia concurrencia.

**Excepción (RN4)**: el cupo `cupo_normal + 1` solo se permite para un **permiso con justificación**. Vacaciones no pueden solicitarse como excepción.

### Grupos de trabajo y su propósito

Los grupos **definen la concurrencia** (cuántos pueden ausentarse al mismo tiempo) y el **compañero de respaldo** obligatorio:

- Cada empleado pertenece a uno o más grupos de trabajo.
- El motor de reglas (`domain.py`) valida el cupo por grupo en cada solicitud.
- Al solicitar una ausencia, el sistema filtra los posibles respaldos mostrando solo compañeros **del mismo grupo**.

| Grupo | Función principal | Miembros | Mín. presentes | Cupo normal |
|-------|-------------------|:--------:|:--------------:|:-----------:|
| G1: Comunicaciones y Atención | Atención al público y comunicaciones | 3 | 2 | 1 |
| G2: Fichas EJPMS | Gestión de fichas judiciales | 3 | 2 | 1 |
| G3: Reparto Const. y Penal | Reparto constitucional y penal | 3 | 2 | 1 |
| G4: Notificaciones y Archivo | Notificaciones y archivo | 2 | 1 | 1 |

> BRIGITH no pertenece a ningún grupo; puede solicitar aplicando solo saldos y respaldo (sin restricción de concurrencia de grupo).

### Calendario de disponibilidad

El calendario muestra el estado de disponibilidad de cada día:

- **Con sesión iniciada**: estado relativo a los grupos del usuario. Si G3 tiene cupo lleno pero G2 está disponible, un empleado de G2 verá ese día como 🟢 Disponible.
- **Sin sesión** (vista pública): vista informativa general — estado más restrictivo entre todos los grupos.

El calendario pinta la ocupación de **todos los grupos**, tanto con sesión como sin ella. Al pasar el cursor sobre un día ocupado, un usuario autenticado ve los **nombres** de quienes están ausentes y, si su propio grupo tiene un estado distinto al global, un aviso `Tu grupo: …` que le indica que aún puede solicitar. Si además el tooltip de grupos está activo (configurable desde el Panel de Coordinación), se muestran también los **grupos** con ausencias. El **motivo y el tipo** de la ausencia nunca se exponen, y sin sesión iniciada no se muestran nombres (RN5, reformulada en PLAN_09).

### Respaldo obligatorio

Toda solicitud requiere designar un compañero de respaldo. El sistema:
1. Filtra automáticamente los compañeros del mismo grupo.
2. Bloquea la solicitud si no hay compañeros disponibles en el grupo.
3. No valida disponibilidad del respaldo (es un acuerdo previo entre empleados, RN6).

---

## ⚖️ Licencia
Este proyecto es una herramienta de uso interno para dependencias judiciales de la República de Colombia.
