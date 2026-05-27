from app.auth import get_password_hash
from app.database import SessionLocal, init_db
from app.models import Empleado


def seed() -> None:
    init_db()
    db = SessionLocal()
    
    # Check if admin already exists
    admin = db.query(Empleado).filter_by(correo="admin@test.com").first()
    if not admin:
        print("Creando usuario de coordinación...")
        admin = Empleado(
            nombre="Administrador",
            correo="admin@test.com",
            password_hash=get_password_hash("admin123"),
            rol="coordinacion"
        )
        db.add(admin)
    
    # Check if employee already exists
    emp = db.query(Empleado).filter_by(correo="empleado@test.com").first()
    if not emp:
        print("Creando usuario empleado...")
        emp = Empleado(
            nombre="Juan Empleado",
            correo="empleado@test.com",
            password_hash=get_password_hash("juan123"),
            rol="empleado"
        )
        db.add(emp)
    
    db.commit()
    db.close()
    print("Seed completado.")

if __name__ == "__main__":
    seed()
