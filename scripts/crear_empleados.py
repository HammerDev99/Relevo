"""Alta manual de empleados desde la consola del contenedor.

Uso (dentro del contenedor relevo-api):
    python -m scripts.crear_empleados NOMBRE:correo:password [NOMBRE:correo:password ...]

Crea empleados con rol 'empleado' y sin grupos asignados. El rol y los
grupos se ajustan luego desde el panel de Coordinacion en la GUI.

Es idempotente: si el correo ya existe, no lo duplica ni lo modifica.

NOTA: solucion temporal mientras no exista POST /coordinacion/usuarios.
"""

import sys

from app.auth import get_password_hash
from app.database import SessionLocal, init_db
from app.models import Empleado

ROL_POR_DEFECTO = "empleado"
LONGITUD_MINIMA_PASSWORD = 8


def parsear(spec: str) -> tuple[str, str, str]:
    """Convierte 'NOMBRE:correo:password' en sus tres partes."""
    partes = spec.split(":")
    if len(partes) != 3:
        raise ValueError(
            f"Formato invalido: {spec!r}. Se espera NOMBRE:correo:password"
        )

    nombre, correo, password = (p.strip() for p in partes)

    if not nombre or not correo or not password:
        raise ValueError(f"Campos vacios en: {spec!r}")
    if "@" not in correo:
        raise ValueError(f"Correo invalido: {correo!r}")
    if len(password) < LONGITUD_MINIMA_PASSWORD:
        raise ValueError(
            f"Password de {nombre} muy corta "
            f"(minimo {LONGITUD_MINIMA_PASSWORD} caracteres)"
        )

    return nombre, correo, password


def crear(specs: list[str]) -> int:
    """Crea los empleados indicados. Retorna codigo de salida."""
    try:
        parseados = [parsear(s) for s in specs]
    except ValueError as e:
        print(f"ERROR: {e}")
        return 1

    correos = [c for _, c, _ in parseados]
    if len(set(correos)) != len(correos):
        print("ERROR: hay correos repetidos en los argumentos")
        return 1

    init_db()
    db = SessionLocal()
    creados = 0
    try:
        for nombre, correo, password in parseados:
            if db.query(Empleado).filter_by(correo=correo).first():
                print(f"OMITIDO  {nombre} <{correo}> ya existe")
                continue

            db.add(Empleado(
                nombre=nombre,
                correo=correo,
                password_hash=get_password_hash(password),
                rol=ROL_POR_DEFECTO,
            ))
            creados += 1
            print(f"CREADO   {nombre} <{correo}> rol={ROL_POR_DEFECTO}")

        db.commit()
    except Exception as e:
        db.rollback()
        print(f"ERROR: no se pudo completar el alta, sin cambios: {e}")
        return 1
    finally:
        db.close()

    print(f"\nListo: {creados} empleado(s) creado(s).")
    if creados:
        print("Asigna rol y grupos desde Coordinacion > Personal de la Oficina.")
    return 0


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)
    sys.exit(crear(sys.argv[1:]))
