# Guía de Despliegue — Relevo v1

Este sistema está diseñado para correr en un VPS de la Rama Judicial mediante **EasyPanel** o **Docker Compose** directo.

## 1. Requisitos
- Docker y Docker Compose instalados en el VPS.
- Puerto 8000 libre (o configurado en el proxy inverso).

## 2. Despliegue con EasyPanel (Recomendado)
1. Crea un nuevo proyecto en EasyPanel.
2. Agrega un servicio de tipo **App**.
3. En **Source**, selecciona tu repositorio de GitHub.
4. En **Build**, EasyPanel detectará automáticamente el `Dockerfile`.
5. En **Environment Variables**, agrega:
   - `SECRET_KEY`: Una cadena aleatoria larga para firmar sesiones.
   - `DATABASE_URL`: `sqlite:////data/relevo.db`
6. En **Storage**, crea un volumen montado en:
   - Path: `/data`
   - Esto garantiza que la base de datos no se pierda al reiniciar el container.

## 3. Despliegue con Docker Compose (Manual)
1. Clona el repositorio en el VPS.
2. Copia el archivo `.env.example` a `.env` y edita la `SECRET_KEY`.
3. Ejecuta:
   ```bash
   docker-compose up -d --build
   ```
4. La aplicación estará disponible en el puerto 8000.

## 4. Inicialización de datos
Para crear el usuario administrador inicial, una vez el container esté corriendo:
```bash
docker exec -it <container_id> python -m src.app.seed
```

## 5. Notas de Seguridad
- Las cookies están configuradas como `HttpOnly` y `SameSite=Strict`.
- Se recomienda usar un certificado SSL (HTTPS) en el VPS; EasyPanel gestiona Let's Encrypt automáticamente.
