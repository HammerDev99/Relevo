from app.auth import get_password_hash
from app.database import SessionLocal, init_db
from app.models import ConfiguracionApp, Empleado, Grupo


def seed() -> None:
    init_db()
    db = SessionLocal()
    
    # 1. Crear el usuario ADMINISTRADOR adicional (COORDINADOR)
    admin_correo = "coordinador@test.com"
    admin = db.query(Empleado).filter_by(correo=admin_correo).first()
    if not admin:
        print("Creando usuario Coordinador Administrador...")
        admin = Empleado(
            nombre="COORDINADOR GENERAL",
            correo=admin_correo,
            password_hash=get_password_hash("admin123"),
            rol="coordinacion"
        )
        db.add(admin)

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
        else:
            g.min_presentes = min_p # Asegurar parámetros
        grupos_db[nombre] = g

    # 3. Lista de empleados reales (TODOS con rol 'empleado')
    # Mapeo de grupos: nombre -> lista de nombres de grupos
    empleados_mapping = {
        "JORGE": ["G3: Reparto Const. y Penal"],
        "YESENIA": ["G3: Reparto Const. y Penal"],
        "FABIAN": ["G4: Notificaciones y Archivo"],
        "BRIGITH": ["G3: Reparto Const. y Penal"], # Asignada a G3 por defecto
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
        
        # Asignar grupos
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
