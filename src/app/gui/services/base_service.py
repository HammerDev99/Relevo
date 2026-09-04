"""Base compartida de los servicios GUI (SPEC-S19-B2).

Antes, los cuatro servicios repetían el mismo bloque
`try / httpx.Client(base_url) / status_code == 200 / except → st.error` en
19 métodos: **Duplicate Code** estructural (AUDIT_11 H14). Además, cada método
decidía por su cuenta si mostrar el error o fallar en silencio.

Esta clase centraliza transporte, cabeceras de sesión y manejo de error.
Los servicios concretos conservan sus firmas públicas: las páginas no cambian.
"""

from typing import Any

import httpx
import streamlit as st

from app.gui import session_keys
from relevo.logger import get_logger

logger = get_logger(__name__)

BASE_URL_POR_DEFECTO = "http://relevo-api:8000"
TIMEOUT_SEGUNDOS = 10.0


class BaseAPIService:
    """Transporte HTTP común a los servicios que consumen la API."""

    def __init__(self, base_url: str = BASE_URL_POR_DEFECTO) -> None:
        self.base_url = base_url

    def get_auth_headers(self) -> dict[str, str]:
        """Cabeceras con la cookie de sesión, si hay una activa."""
        token = st.session_state.get(session_keys.AUTH_TOKEN)
        return {"Cookie": f"session={token}"} if token else {}

    def _request(
        self,
        metodo: str,
        ruta: str,
        *,
        json: Any = None,
        data: Any = None,
        params: Any = None,
        autenticado: bool = True,
        mostrar_error: bool = True,
        mensaje_error: str | None = None,
        follow_redirects: bool = False,
    ) -> httpx.Response | None:
        """Ejecuta una petición y devuelve la respuesta, o `None` si falla la red.

        Un fallo de transporte (servidor caído, timeout) devuelve `None`. Una
        respuesta con código de error se devuelve tal cual: decidir qué hacer
        con un 400 o un 403 corresponde a cada servicio.
        """
        headers = self.get_auth_headers() if autenticado else {}
        try:
            with httpx.Client(base_url=self.base_url, timeout=TIMEOUT_SEGUNDOS) as client:
                return client.request(
                    metodo,
                    ruta,
                    json=json,
                    data=data,
                    params=params,
                    headers=headers,
                    follow_redirects=follow_redirects,
                )
        except Exception as e:
            # AUDIT_12 H4: el detalle técnico (URL interna del API, tipo de
            # excepción) va al log, no a la pantalla del usuario.
            logger.warning("Fallo de transporte en %s %s: %s", metodo, ruta, e)
            if mostrar_error:
                st.error(mensaje_error or "No se pudo conectar con el servidor.")
            return None

    def _get_json(
        self,
        ruta: str,
        *,
        params: Any = None,
        por_defecto: Any = None,
        autenticado: bool = True,
        mostrar_error: bool = False,
        mensaje_error: str | None = None,
    ) -> Any:
        """GET que devuelve el JSON, o `por_defecto` ante cualquier fallo."""
        respuesta = self._request(
            "GET", ruta, params=params, autenticado=autenticado,
            mostrar_error=mostrar_error, mensaje_error=mensaje_error,
        )
        if respuesta is not None and respuesta.status_code == 200:
            return respuesta.json()
        return por_defecto

    def _detalle_error(self, respuesta: httpx.Response, por_defecto: str) -> str:
        """Extrae `detail` del cuerpo de error; cae al mensaje por defecto."""
        try:
            detalle = respuesta.json().get("detail")
        except Exception:
            return por_defecto
        return str(detalle) if detalle else por_defecto
