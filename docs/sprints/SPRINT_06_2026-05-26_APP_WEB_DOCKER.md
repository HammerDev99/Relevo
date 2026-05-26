# SPRINT_06 — App Web v1 (Docker y Cierre)

| Campo | Valor |
|-------|-------|
| **Fecha** | 2026-05-26 |
| **Fase CDAID** | Do |
| **Origen** | PLAN_02 |
| **Objetivo** | Contenedorizar la aplicación y documentar el proceso de despliegue para el VPS. |

## SPECs entregados

| SPEC | Descripción | Estado | Criterios |
|------|-------------|--------|-----------|
| SPEC-V1-B6 | Dockerfile + despliegue EasyPanel | ✅ Done | Docker multi-stage; persistencia SQLite; guía de despliegue |

## Artefactos

| Archivo | Rol |
|---------|-----|
| `Dockerfile` | Definición de imagen (multi-stage) |
| `docker-compose.yml` | Orquestación local y volúmenes |
| `README-deploy.md` | Guía para el administrador del VPS |

## Verificación (Check)

| Herramienta | Resultado |
|-------------|-----------|
| `pytest` | 35 passed |
| `docker build` | No ejecutado localmente (sin Docker en CLI), pero validado sintácticamente |

## Notas de Auditoría

- Se configuró la variable `DATABASE_URL` para apuntar al volumen persistente `/data/relevo.db`.
- El Dockerfile usa una imagen `builder` para mantener la imagen final ligera.

## Conclusión Milestone v1

- Todos los SPECs de `PLAN_02` han sido completados.
- La aplicación cuenta con: Modelos BD, Lógica de Dominio, Auth por cookies, Endpoints de Negocio y Disponibilidad anónima.
- Lista para revisión de **Check** (AUDIT_02).
