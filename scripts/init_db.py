"""
Script de inicialización de la base de datos.
Crea todas las tablas y carga datos iniciales (roles, permisos, usuario admin).

Uso:
    python scripts/init_db.py
"""
import sys, os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from datetime import datetime, date
from app import create_app, db, bcrypt
from app.models import Usuario, Rol, Permiso
from app.decorators import PERMISOS, PERMISOS_POR_ROL

app = create_app()

def init_db():
    with app.app_context():
        print("▶  Creando tablas...")
        db.create_all()
        print("✓  Tablas creadas.")

        # ── Permisos ──────────────────────────────────────────
        print("▶  Cargando permisos...")
        for clave, desc in PERMISOS.items():
            if not Permiso.query.filter_by(permiso=clave).first():
                db.session.add(Permiso(permiso=clave, descripcion=desc, creado=datetime.utcnow()))
        db.session.commit()
        print(f"✓  {len(PERMISOS)} permisos registrados.")

        # ── Roles ─────────────────────────────────────────────
        print("▶  Cargando roles...")
        descripciones = {
            'administrador': 'Acceso total al sistema',
            'profesor':      'Gestión de calificaciones',
            'estudiante':    'Consulta de notas y pagos propios',
            'consulta':      'Solo lectura en todos los módulos',
            'transcriptor':  'Registro de alumnos, notas y pagos',
        }
        for nombre, perms_clave in PERMISOS_POR_ROL.items():
            rol = Rol.query.filter_by(rol=nombre).first()
            if not rol:
                rol = Rol(rol=nombre, descripcion=descripciones.get(nombre, ''),
                          creado=datetime.utcnow())
                db.session.add(rol)
                db.session.flush()
            # Asignar permisos
            rol.permisos = []
            for clave in perms_clave:
                p = Permiso.query.filter_by(permiso=clave).first()
                if p:
                    rol.permisos.append(p)
        db.session.commit()
        print("✓  5 roles registrados con sus permisos.")

        # ── Usuario administrador ──────────────────────────────
        print("▶  Creando usuario administrador...")
        if not Usuario.query.filter_by(usuario='admin').first():
            hashed = bcrypt.generate_password_hash('admin123').decode('utf-8')
            admin = Usuario(
                usuario='admin',
                email='admin@uaded.edu',
                password=hashed,
                activo=True,
                last_login=date.today(),
                creado=datetime.utcnow()
            )
            rol_admin = Rol.query.filter_by(rol='administrador').first()
            if rol_admin:
                admin.roles.append(rol_admin)
            db.session.add(admin)
            db.session.commit()
            print("✓  Usuario admin creado  →  usuario: admin  |  contraseña: admin123")
        else:
            print("   (El usuario admin ya existe, se omite.)")

        print("\n✅  Base de datos inicializada correctamente.")
        print("   ⚠️  Cambie la contraseña del administrador tras el primer inicio de sesión.")

if __name__ == '__main__':
    init_db()
