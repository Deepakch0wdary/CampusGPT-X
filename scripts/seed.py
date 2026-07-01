import sys
from pathlib import Path
import uuid
from passlib.context import CryptContext

# Resolve backend module structures
backend_root = Path(__file__).resolve().parent.parent / "apps" / "backend"
if str(backend_root) not in sys.path:
    sys.path.insert(0, str(backend_root))

from app.core.dependencies import SessionLocal
from app.models.models import Role, Permission, User, UserPermission
from app.core.security import get_password_hash

ROLES = [
    "MASTER_ADMIN",
    "TEACHER",
    "MENTOR",
    "PLACEMENT_OFFICER",
    "ADMISSION_OFFICE",
    "STUDENT",
    "PARENT",
    "ALUMNI",
    "LIBRARIAN",
    "HOSTEL_MANAGER",
    "TRANSPORT_MANAGER"
]

PERMISSIONS = [
    "users:create",
    "users:read",
    "users:update",
    "users:delete",
    "roles:manage",
    "sessions:manage",
    "audits:read"
]

def seed():
    print("[i] Initializing system seeding...")
    db = SessionLocal()
    try:
        # Seed default Roles
        db_roles = {}
        for role_name in ROLES:
            existing = db.query(Role).filter_by(name=role_name).first()
            if not existing:
                role = Role(id=str(uuid.uuid4()), name=role_name, description=f"{role_name} System Role")
                db.add(role)
                db_roles[role_name] = role
                print(f"[+] Role created: {role_name}")
            else:
                db_roles[role_name] = existing

        # Seed default Permissions
        db_permissions = {}
        for perm_name in PERMISSIONS:
            existing = db.query(Permission).filter_by(name=perm_name).first()
            if not existing:
                perm = Permission(id=str(uuid.uuid4()), name=perm_name, description=f"Ability to execute {perm_name}")
                db.add(perm)
                db_permissions[perm_name] = perm
                print(f"[+] Permission created: {perm_name}")
            else:
                db_permissions[perm_name] = existing

        db.commit()

        # Seed the single Master Admin account
        admin_role = db_roles["MASTER_ADMIN"]
        existing_admin = db.query(User).filter_by(roleId=admin_role.id).first()
        
        if not existing_admin:
            admin_id = str(uuid.uuid4())
            admin_email = "admin@campusgpt.com"
            admin_username = "admin"
            temp_password = "AdminPassword@123"
            hashed_pwd = get_password_hash(temp_password)

            admin = User(
                id=admin_id,
                email=admin_email,
                username=admin_username,
                passwordHash=hashed_pwd,
                name="Master Admin",
                roleId=admin_role.id,
                mustChangePassword=True,
                verified=True
            )
            db.add(admin)
            db.commit()
            print(f"[✔] MASTER ADMIN ACCOUNT SEEDED: {admin_email} / {temp_password}")

            # Assign all direct permissions to Master Admin
            for perm in db_permissions.values():
                link = UserPermission(
                    id=str(uuid.uuid4()),
                    userId=admin_id,
                    permissionId=perm.id
                )
                db.add(link)
            db.commit()
            print("[✔] Granted all permissions to Master Admin.")
        else:
            print("[i] Master Admin account already exists. Skipping seeder to enforce MASTER_ADMIN_COUNT = 1.")

    except Exception as e:
        print(f"[✘] Error seeding database: {e}")
        db.rollback()
    finally:
        db.close()
        print("[i] Seeding sequence finished.")

if __name__ == "__main__":
    seed()
