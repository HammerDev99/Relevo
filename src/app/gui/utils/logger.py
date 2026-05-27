import functools
from collections.abc import Callable
from typing import Any, TypeVar

import streamlit as st

from relevo.logger import get_logger

logger = get_logger("relevo.gui")

F = TypeVar("F", bound=Callable[..., Any])

def log_gui_action(service_name: str) -> Callable[[F], F]:
    """
    Decorador para servicios de la GUI que registra peticiones y errores.
    Incluye contexto del usuario si está autenticado.
    """
    def decorator(func: F) -> F:
        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            user = st.session_state.get("user_email", "anonymous")
            try:
                # Evitamos loguear 'self' (args[1:])
                logger.info(f"[{user}] GUI_CALL {service_name}.{func.__name__} args={args[1:]}")
                result = func(*args, **kwargs)
                return result
            except Exception as e:
                logger.error(
                    f"[{user}] GUI_ERROR {service_name}.{func.__name__}: {str(e)}", 
                    exc_info=True
                )
                raise e
        return wrapper # type: ignore
    return decorator
