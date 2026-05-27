from app.auth import get_password_hash
from app.database import SessionLocal, init_db
from app.models import Empleado


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

    # 2. Lista de empleados reales (TODOS con rol 'empleado')
    empleados_data = [
        ("JORGE", "jorge@test.com", "jorge123"),
        ("YESENIA", "yesenia@test.com", "yesenia123"),
        ("FABIAN", "fabian@test.com", "fabian123"),
        ("BRIGITH", "brigith@test.com", "brigith123"),
        ("DANIELA", "daniela@test.com", "daniela123"),
        ("JACKSON", "jackson@test.com", "jackson123"),
        ("FLOR", "flor@test.com", "flor123"),
        ("AMERICA", "america@test.com", "america123"),
        ("NELLY", "nelly@test.com", "nelly123"),
        ("HECTOR", "hector@test.com", "hector123"),
        ("DANIEL", "daniel@test.com", "daniel123"),
    ]
    
    print("Sincronizando empleados de la oficina...")
    
    for nombre, correo, password in empleados_data:
        existente = db.query(Empleado).filter_by(correo=correo).first()
        if not existente:
            print(f"Creando usuario empleado: {nombre}")
            nuevo = Empleado(
                nombre=nombre,
                correo=correo,
                password_hash=get_password_hash(password),
                rol="empleado" # Todos son empleados
            )
            db.add(nuevo)
        else:
            # Asegurar que si existían antes, ahora tengan rol empleado
            if existente.rol != "empleado" and existente.correo != admin_correo:
                existente.rol = "empleado"
                print(f"Normalizando rol de {nombre} a empleado.")
    
    db.commit()
    db.close()
    print("Seed de oficina (limpio) completado.")

if __name__ == "__main__":
    seed()
