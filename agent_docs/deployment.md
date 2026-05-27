# Infraestructura de Despliegue — Relevo

Este documento detalla los mecanismos para exponer y desplegar la aplicación Relevo.

## 1. Demo Rápida (Cloudflare Tunnel)

Para pruebas rápidas sin configuración de servidor, se utiliza **Cloudflare Quick Tunnels**.

### Archivos Relacionados
- `docker-compose.tunnel.yml`: Define los servicios `api`, `gui` y el contenedor `tunnel` que solicita la URL pública.
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
