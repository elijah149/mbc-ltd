"""
Seeds the database with the MBCU LTD organizational structure:

    Board of Directors (Body Manager)
            -> Manager
                -> Production Manager -> Weighing Officer, Industry Employee
                -> Store Keeper
                -> Accountant Manager -> Accountant Officer -> Accounts Clerk
                -> Operation Manager -> Operation Officer
                -> IT Officer

Run with:  python -m app.seed
"""
from app.core.database import SessionLocal, engine, Base
from app.core.security import hash_password
from app.core.config import settings
import app.models  # noqa: F401
from app.models.user import User, Role, Permission, RolePermission, Department, UserStatus

PERMISSIONS = [
    "create_staff", "delete_staff", "approve_payments", "manage_inventory",
    "manage_finance", "manage_users", "manage_production", "view_reports", "export_reports",
]

DEPARTMENTS = ["Production", "Store", "Finance", "Operations", "IT"]

# name -> (level, reports_to_name, [permissions])
ROLES: dict[str, dict] = {
    "Board Director":     {"level": 0, "reports_to": None,              "permissions": PERMISSIONS},
    "Manager":            {"level": 1, "reports_to": "Board Director",  "permissions": PERMISSIONS},
    "Production Manager": {"level": 2, "reports_to": "Manager",         "permissions": ["manage_production", "view_reports", "create_staff"]},
    "Store Keeper":       {"level": 2, "reports_to": "Manager",         "permissions": ["manage_inventory", "view_reports"]},
    "Accountant Manager": {"level": 2, "reports_to": "Manager",         "permissions": ["manage_finance", "approve_payments", "view_reports", "export_reports"]},
    "Operation Manager":  {"level": 2, "reports_to": "Manager",         "permissions": ["view_reports", "create_staff"]},
    "IT Officer":         {"level": 2, "reports_to": "Manager",         "permissions": ["manage_users", "view_reports"]},
    "Weighing Officer":   {"level": 3, "reports_to": "Production Manager", "permissions": ["manage_production"]},
    "Industry Employee":  {"level": 3, "reports_to": "Production Manager", "permissions": []},
    "Accountant Officer": {"level": 3, "reports_to": "Accountant Manager", "permissions": ["manage_finance", "approve_payments"]},
    "Accounts Clerk":     {"level": 4, "reports_to": "Accountant Officer", "permissions": ["manage_finance"]},
    "Operation Officer":  {"level": 3, "reports_to": "Operation Manager",  "permissions": ["view_reports"]},
}


def seed():
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        # 1. Departments
        dept_objs = {}
        for name in DEPARTMENTS:
            dept = db.query(Department).filter_by(name=name).first()
            if not dept:
                dept = Department(name=name)
                db.add(dept)
                db.flush()
            dept_objs[name] = dept

        # 2. Permissions
        perm_objs = {}
        for name in PERMISSIONS:
            perm = db.query(Permission).filter_by(name=name).first()
            if not perm:
                perm = Permission(name=name)
                db.add(perm)
                db.flush()
            perm_objs[name] = perm

        # 3. Roles (two passes: create all, then wire reports_to)
        role_objs = {}
        for name, cfg in ROLES.items():
            role = db.query(Role).filter_by(name=name).first()
            if not role:
                role = Role(name=name, level=cfg["level"])
                db.add(role)
                db.flush()
            role_objs[name] = role

        for name, cfg in ROLES.items():
            role = role_objs[name]
            if cfg["reports_to"]:
                role.reports_to_role_id = role_objs[cfg["reports_to"]].id
            for perm_name in cfg["permissions"]:
                exists = (
                    db.query(RolePermission)
                    .filter_by(role_id=role.id, permission_id=perm_objs[perm_name].id)
                    .first()
                )
                if not exists:
                    db.add(RolePermission(role_id=role.id, permission_id=perm_objs[perm_name].id))

        db.commit()

        # 4. First superuser (Board Director / system admin)
        admin = db.query(User).filter_by(email=settings.FIRST_SUPERUSER_EMAIL).first()
        if not admin:
            admin = User(
                fullname="System Administrator",
                email=settings.FIRST_SUPERUSER_EMAIL,
                password_hash=hash_password(settings.FIRST_SUPERUSER_PASSWORD),
                role_id=role_objs["Board Director"].id,
                is_superuser=True,
                status=UserStatus.active,
            )
            db.add(admin)
            db.commit()
            print(f"Created first superuser: {settings.FIRST_SUPERUSER_EMAIL} / {settings.FIRST_SUPERUSER_PASSWORD}")
        else:
            print("Superuser already exists, skipping.")

        print("Seed complete: departments, roles, permissions, and hierarchy are in place.")
    finally:
        db.close()


if __name__ == "__main__":
    seed()
