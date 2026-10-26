from database import engine, SessionLocal, Base, Admin
from werkzeug.security import generate_password_hash

Base.metadata.create_all(bind=engine)
db = SessionLocal()

try:
    admins_to_add = [
        ("admin123", "admin@gmail.com", 1),
    ]

    for password, email, is_active in admins_to_add:
        existing_admin = db.query(Admin).filter(Admin.email == email).first()
        if existing_admin:
            print(f"Admin already exists! Email: {existing_admin.email}")
        else:
            hashed_password = generate_password_hash(password)
            new_admin = Admin(username=email, password=hashed_password, email=email, is_active=is_active)
            db.add(new_admin)
            db.commit()
            db.refresh(new_admin)
            print(f"Admin created successfully! Email: {new_admin.email}")

    db.commit()
except Exception as e:
    print(f"Error: {e}")
    db.rollback()
finally:
    db.close()
