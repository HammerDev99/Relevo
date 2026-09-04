import os

from app.auth import get_password_hash
from app.database import SessionLocal, init_db
from app.models import ConfiguracionApp, Empleado, Grupo

# AUDIT-H7: la contraseña inicial de las cuentas de coordinación no debe estar
# en el código. Se toma de RELEVO_SEED_PASSWORD; el fallback solo aplica en
# desarrollo y debe rotarse desde Mi Perfil tras el primer ingreso.
_PASSWORD_COORDINACION = os.getenv("RELEVO_SEED_PASSWORD", "cambiar-en-produccion")


def seed() -> None:
    init_db()
    db = SessionLocal()

    # 1. Coordinadores
    # LUISA y JOHN se retiraron del seed el 2026-09-04: ya existen en
    # producción con su contraseña rotada, y volver a listarlos solo los
    # recrearía con la credencial por defecto si alguna vez se eliminaran.
    # Las altas de coordinación se hacen desde el panel (SPEC-S18-B4).
    coordinadores = [
        ("COORDINADOR GENERAL", "coordinador@test.com", _PASSWORD_COORDINACION),
    ]
    for nombre, correo, password in coordinadores:
        if not db.query(Empleado).filter_by(correo=correo).first():
            print(f"Creando coordinador: {nombre}")
            db.add(Empleado(
                nombre=nombre,
                correo=correo,
                password_hash=get_password_hash(password),
                rol="coordinacion",
            ))

    # 2. Definición de Grupos (PLAN_05)
    grupos_data = {
        "G1: Comunicaciones y Atención": 2,
        "G2: Fichas EJPMS": 2,
        "G3: Reparto Const. y Penal": 2,
        "G4: Notificaciones y Archivo": 1,
    }
    
    grupos_db = {}
    for nombre, min_p in grupos_data.items():
        g = db.query(Grupo).filter_by(nombre=nombre).first()
        if not g:
            print(f"Creando grupo: {nombre}")
            g = Grupo(nombre=nombre, min_presentes=min_p)
            db.add(g)
        # SPEC-S18-C1: si el grupo ya existe se respeta su min_presentes.
        # El seed corre en cada arranque del contenedor; sobrescribirlo
        # revertiría los cupos (RN3) ajustados desde el panel.
        grupos_db[nombre] = g

    # 3. Lista de empleados reales (TODOS con rol 'empleado')
    # Mapeo de grupos: nombre -> lista de nombres de grupos
    empleados_mapping = {
        "JORGE": ["G3: Reparto Const. y Penal"],
        "YESENIA": ["G3: Reparto Const. y Penal"],
        "FABIAN": ["G4: Notificaciones y Archivo"],
        "BRIGITH": [],  # Sin grupo asignado (decisión 2026-06-02)
        "DANIELA": ["G3: Reparto Const. y Penal"],
        "JACKSON": ["G2: Fichas EJPMS"],
        "FLOR": ["G1: Comunicaciones y Atención"],
        "AMERICA": ["G2: Fichas EJPMS"],
        "NELLY": ["G1: Comunicaciones y Atención"],
        "HECTOR": ["G1: Comunicaciones y Atención", "G4: Notificaciones y Archivo"], # Multi-grupo
        "DANIEL": ["G2: Fichas EJPMS"],
    }
    
    print("Sincronizando empleados y grupos...")
    
    for nombre, grp_nombres in empleados_mapping.items():
        correo = f"{nombre.lower()}@test.com"
        password = f"{nombre.lower()}123"
        
        user = db.query(Empleado).filter_by(correo=correo).first()
        if not user:
            print(f"Creando usuario empleado: {nombre}")
            user = Empleado(
                nombre=nombre,
                correo=correo,
                password_hash=get_password_hash(password),
                rol="empleado"
            )
            db.add(user)
            # SPEC-S18-C1: los grupos solo se asignan al crear el empleado.
            # Reasignarlos en cada arranque revertía los cambios hechos
            # desde Coordinación > Personal de la Oficina.
            user.grupos = [grupos_db[gn] for gn in grp_nombres]
    
    # 4. Configuración global (singleton id=1)
    config = db.get(ConfiguracionApp, 1)
    if not config:
        print("Creando configuración global...")
        db.add(ConfiguracionApp(id=1, mostrar_grupos_tooltip=True))

    db.commit()
    db.close()
    print("Seed de oficina (Autogestión V3) completado.")

if __name__ == "__main__":
    seed()
