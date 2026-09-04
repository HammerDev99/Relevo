"""Roles de usuario del sistema (SPEC-S19-A2).

Fuente única de los identificadores de rol. Antes el literal `"coordinacion"`
estaba disperso entre `auth.py`, `seed.py`, los schemas y la GUI: renombrarlo
habría exigido *Shotgun Surgery*.
"""

from typing import Literal

# Alias compartido por UsuarioCreate y UsuarioUpdate (SPEC-S19-A1): la whitelist
# se declara una sola vez y ambos contratos quedan simétricos.
RolUsuario = Literal["empleado", "coordinacion"]

# Anotadas con el alias para que mypy las acepte como default de un campo
# tipado `RolUsuario` (sin la anotación se infieren como `str`).
ROL_EMPLEADO: RolUsuario = "empleado"
ROL_COORDINACION: RolUsuario = "coordinacion"
