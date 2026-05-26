"""Fábrica de loggers del proyecto.

Usar siempre `get_logger(__name__)`, nunca `logging.getLogger` directo.
"""

from __future__ import annotations

import logging

_FORMATO = "%(asctime)s | %(levelname)s | %(name)s | %(message)s"


def get_logger(name: str) -> logging.Logger:
    """Retorna un logger configurado con handler de consola (idempotente)."""
    logger = logging.getLogger(name)
    if not logger.handlers:
        handler = logging.StreamHandler()
        handler.setFormatter(logging.Formatter(_FORMATO))
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)
    return logger
