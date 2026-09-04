# Guía de Despliegue — Relevo v1 (Estándar VPS)

Este sistema sigue los estándares de contenedorización de la Rama Judicial (basado en Sherlock Docs).

## 1. Requisitos
- Docker y Docker Compose instalados en el VPS.
- Puerto 8000 libre.

## 2. Configuración en EasyPanel
1. Crea un nuevo servicio **App**.
2. **Build**: EasyPanel usará el `Dockerfile` optimizado (2-stage).
3. **Environment Variables**:
   - `SECRET_KEY`: Requerido (mínimo 32 caracteres).
   - `TZ`: `America/Bogota` (default).
4. **Storage** (Volúmenes):
   - Monta un volumen en `/app/data` para persistencia de la base de datos.
   - Monta un volumen en `/app/logs` para auditoría.

## 3. Inicialización Automática
El contenedor usa un `docker-entrypoint.sh` que realiza las siguientes tareas al arrancar:
- Ajusta permisos de los volúmenes montados (usuario `relevo` no-root).
- Ejecuta el script de **Seed** (`src/app/seed.py`) para asegurar que el usuario administrador (`admin@test.com`) existe.

## 4. Despliegue Manual (Compose)
```bash
# Clonar y levantar
docker-compose up -d --build

# Ver logs
docker-compose logs -f
```

## 5. Salud del Sistema
El contenedor incluye un `HEALTHCHECK` que consulta la raíz cada 30 segundos. Si el servicio no responde, Docker/EasyPanel intentarán reiniciarlo.

## 6. Migración de Datos (v2 a v3)
Dado que Relevo emplea una base de datos local SQLite en un volumen persistente (`/app/data`), **preservar los datos de producción** (usuarios existentes y el historial de solicitudes) es fundamental.

Al desplegar la versión v3 (Autogestión por Grupos), SQLAlchemy creará automáticamente las nuevas tablas (`grupos` y la tabla intermedia `empleado_grupo`) de forma **no destructiva**. Las tablas existentes no se borrarán.

Para que los usuarios actuales mantengan la coherencia con el nuevo motor de concurrencia:
1. El script `src/app/seed.py` se ejecuta automáticamente al iniciar el contenedor gracias a `docker-entrypoint.sh`.
2. Dicho script valida si el usuario ya existe y **no lo modifica**: contraseña, rol y grupos se conservan. Los grupos del mapeo base solo se asignan al **crear** un empleado por primera vez (SPEC-S18-C1), de modo que los reinicios del contenedor no revierten los ajustes hechos desde el panel de Coordinación.
3. El historial de `Solicitud` no se altera, manteniendo la continuidad de la trazabilidad. No se requieren scripts manuales de SQL (ALTER TABLE) adicionales.

## 7. Despliegue VPS (EasyPanel + Docker Compose)

### Nombres de Servicios
- Servicio GUI: `relevo-gui` (dominio: relevo.sprintjudicial.com, puerto 8501)
- Servicio API: `relevo-api` (sin dominio, puerto 8000, acceso interno)

### Comunicación Interna
La GUI se comunica con la API usando el nombre del servicio Docker:
- URL base API: `http://relevo-api:8000`
- Health check API: `http://relevo-api:8000/`

### Variables de Entorno (EasyPanel)
**Ambos servicios:**
- `SECRET_KEY`: Clave secreta mínimo 32 caracteres
- `DATABASE_URL=sqlite:////app/data/database/relevo.db`
- `TZ=America/Bogota`

**Solo GUI:**
- `RELEVO_MODE=gui`

**Solo API:**
- `RELEVO_MODE=api`

### Volúmenes (EasyPanel)
Montar los mismos volúmenes en ambos servicios para compartir la base de datos SQLite:
- Host: `/etc/easypanel/projects/sprintjudicial/relevo-gui/volumes/database` → Container: `/app/data/database`
- Host: `/etc/easypanel/projects/sprintjudicial/relevo-gui/volumes/logs` → Container: `/app/logs`

### Recursos Recomendados
- GUI: 512 MB RAM
- API: 256 MB RAM
