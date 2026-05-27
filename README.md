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

### Usuarios de Prueba (Seed)
El sistema se inicializa automáticamente con:
- **Administrador**: `admin@test.com` / `admin123`
- **Empleado**: `empleado@test.com` / `juan123`

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

## ⚖️ Licencia
Este proyecto es una herramienta de uso interno para dependencias judiciales de la República de Colombia.
