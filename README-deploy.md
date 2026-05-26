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
