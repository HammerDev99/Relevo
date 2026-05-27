# Estándar de Logging — Relevo

## Backend (API)
- Archivo: `logs/api.log`
- Uso: `from relevo.logger import get_logger; logger = get_logger(__name__)`
- Niveles: INFO para flujo normal, ERROR para fallos de validación/negocio, CRITICAL para infraestructura.

## Frontend (GUI)
- Archivo: `logs/gui.log`
- Objetivo: Trazabilidad de la experiencia de usuario y errores de red.
- Implementación (SPRINT 11): Unificado en `app.gui.utils.logger`.
- Cada llamada a un `Service` debe registrar:
  1. Inicio de petición.
  2. Respuesta exitosa (con tiempo de respuesta).
  3. Detalle de error (si ocurre).

## Rotación
- Configurada en el contenedor Docker para evitar saturación de disco en el VPS.
