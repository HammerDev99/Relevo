# Infraestructura de Despliegue — Relevo

Este documento detalla los mecanismos para exponer y desplegar la aplicación Relevo.

## 1. Demo Rápida (Cloudflare Tunnel)

Para pruebas rápidas sin configuración de servidor, se utiliza **Cloudflare Quick Tunnels**.

### Archivos Relacionados
- `docker-compose.tunnel.yml`: Define los servicios `relevo-api`, `relevo-gui` y el contenedor `tunnel` que solicita la URL pública.
- `docker-entrypoint.sh`: Contiene los flags `--server.enableCORS=false` y `--server.enableXsrfProtection=false` necesarios para que Streamlit acepte conexiones a través del túnel.

### Comando de Ejecución
```powershell
docker compose -f docker-compose.tunnel.yml up
```
*Al ejecutarlo, buscar en los logs la URL `https://*.trycloudflare.com`.*

## 2. Persistencia (Base de Datos)

El sistema utiliza **SQLite 3**.

### Fuente de Verdad
- **Ubicación**: `data/database/relevo.db`
- **Configuración Docker**: Este directorio está montado como un volumen persistente.
- **Seguridad**: El archivo está incluido en `.gitignore` para evitar que datos sensibles de los empleados lleguen al repositorio de código.

## 3. Configuración de Módulos (Shadowing Fix)

Para evitar que Python confunda el archivo de entrada con el paquete `app`, se utiliza la siguiente estructura:
- **Paquete Raíz**: `src/app/`
- **Entrada GUI**: `src/app/gui/portal.py` (Renombrado desde `app.py` para evitar colisiones).

## 4. Estrategia de Migración y Preservación de Datos (Transición v2 a v3)

Dado que se introdujeron cambios en el esquema (Nuevas entidades de `Grupo`), el proceso de despliegue en producción debe asegurar la integridad del archivo persistente `relevo.db`.

1. **Esquema No Destructivo**: La directiva `Base.metadata.create_all(bind=engine)` de SQLAlchemy no borra las tablas preexistentes. Exclusivamente agrega las nuevas tablas requeridas por la v3 (`grupos` y `empleado_grupo`).
2. **Backfill de Datos**: Al momento de arrancar la nueva imagen del contenedor, el script `docker-entrypoint.sh` invoca a `src/app/seed.py`. Este script oficia como un migrador automático de estado de producción: 
    - Busca a los empleados preexistentes en la base de datos (por correo electrónico).
    - Mantiene intacta la fila y las contraseñas.
    - Carga en la base de datos las entidades de los nuevos `Grupos`.
    - Establece y actualiza las relaciones Many-to-Many entre los empleados existentes y los nuevos grupos de manera idempotente.
3. **Preservación de Solicitudes**: Las solicitudes históricas (tabla `solicitudes`) mantendrán sus llaves foráneas (`empleado_id`) sin requerir migración de estado ya que el motor v3 evalúa el historial contra el grupo actual del empleado para cálculos en tiempo real.
