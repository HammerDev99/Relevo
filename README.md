# Relevo — Sistema de Gestión de Ausencias

Sistema diseñado para la coordinación de vacaciones y permisos en dependencias judiciales de Colombia. Este MVP permite gestionar las ausencias de hasta 10 empleados garantizando la continuidad del servicio mediante reglas de concurrencia y protegiendo la privacidad del personal.

## 🚀 Características Principales

- **Cálculo de Festivos Colombianos**: Integración con la Ley Emiliani (Ley 51 de 1983) para determinar días hábiles reales.
- **Validación de Reglas de Negocio**:
  - Saldo de 22 días de vacaciones al año.
  - Saldo de 3 días de permiso al mes.
  - Control de concurrencia (máximo 1 ausente estándar, hasta 2 en excepciones).
  - Validación de compañero de respaldo obligatorio.
- **Privacidad (RN5)**: Calendario de disponibilidad anónimo que permite planificar sin exponer datos sensibles.
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

### Concurrencia (toda la oficina)

La regla de concurrencia aplica **globalmente** sobre los 10 empleados, sin distinción de grupo:

| Ausentes simultáneos | Estado del día | Qué significa |
|---------------------|----------------|---------------|
| 0 | 🟢 Disponible | Cupo libre, cualquiera puede ausentarse |
| 1 | 🟡 Ocupado | Ya hay un ausente — se requiere tramitar como **excepción** (RN4) |
| 2 | 🔴 Cupo lleno | No es posible ausentarse ese día |

> **Importante**: si JACKSON (G2) tiene permiso el martes, JORGE (G3) verá ese día como **Ocupado** aunque sean de grupos distintos. Esto es correcto — la oficina funciona como una unidad y el cupo estándar es 1 ausente en total, no 1 por grupo.

### Grupos de trabajo y su propósito

Los grupos **no** definen quién puede ausentarse al mismo tiempo. Su función es determinar el **compañero de respaldo** obligatorio:

- Cada empleado pertenece a uno o más grupos de trabajo.
- Al solicitar una ausencia, el sistema filtra automáticamente los posibles respaldos mostrando solo compañeros **del mismo grupo**.
- Esto garantiza que quien cubre la ausencia conoce las tareas específicas del área.

| Grupo | Función principal | Mín. presentes |
|-------|-------------------|:--------------:|
| G1: Comunicaciones y Atención | Atención al público y comunicaciones | 2 |
| G2: Fichas EJPMS | Gestión de fichas judiciales | 2 |
| G3: Reparto Const. y Penal | Reparto constitucional y penal | 2 |
| G4: Notificaciones y Archivo | Notificaciones y archivo | 1 |

### Calendario de disponibilidad

El calendario es **público** (no requiere iniciar sesión) y muestra el estado global de cada día. Cuando el tooltip de grupos está activo (configurable desde el Panel de Coordinación), al pasar el cursor sobre un día ocupado se muestran los **grupos** con ausencias — nunca nombres ni motivos (RN5: privacidad).

Esto permite que un empleado de G3 identifique, por ejemplo, que el día está ocupado por ausencia de G2, y decida si tramita excepción o elige otra fecha.

### Respaldo obligatorio

Toda solicitud requiere designar un compañero de respaldo. El sistema:
1. Filtra automáticamente los compañeros del mismo grupo.
2. Bloquea la solicitud si no hay compañeros disponibles en el grupo.
3. No valida disponibilidad del respaldo (es un acuerdo previo entre empleados, RN6).

---

## ⚖️ Licencia
Este proyecto es una herramienta de uso interno para dependencias judiciales de la República de Colombia.
