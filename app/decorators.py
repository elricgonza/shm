from functools import wraps
from flask import abort, flash, redirect, url_for
from flask_login import current_user


def role_required(*roles):
    """Permite acceso solo a usuarios con alguno de los roles indicados."""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not current_user.is_authenticated:
                return redirect(url_for('auth.login'))
            if not any(current_user.has_role(r) for r in roles):
                abort(403)
            return f(*args, **kwargs)
        return decorated_function
    return decorator


def permission_required(perm):
    """Permite acceso solo a usuarios con el permiso indicado."""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not current_user.is_authenticated:
                return redirect(url_for('auth.login'))
            if not current_user.has_permission(perm):
                abort(403)
            return f(*args, **kwargs)
        return decorated_function
    return decorator


# Roles disponibles
ROLES = {
    'administrador': 'Administrador',
    'profesor':      'Profesor',
    'estudiante':    'Estudiante',
    'consulta':      'Consulta',
    'transcriptor':  'Transcriptor',
}

# Permisos disponibles por módulo
PERMISOS = {
    # Gestión
    'gestion_ver':    'Ver gestiones académicas',
    'gestion_crear':  'Crear gestión académica',
    'gestion_editar': 'Editar gestión académica',
    'gestion_borrar': 'Eliminar gestión académica',
    # Grado
    'grado_ver':    'Ver grados',
    'grado_crear':  'Crear grado',
    'grado_editar': 'Editar grado',
    'grado_borrar': 'Eliminar grado',
    # Materia
    'materia_ver':    'Ver materias',
    'materia_crear':  'Crear materia',
    'materia_editar': 'Editar materia',
    'materia_borrar': 'Eliminar materia',
    # Profesor
    'profesor_ver':    'Ver profesores',
    'profesor_crear':  'Crear profesor',
    'profesor_editar': 'Editar profesor',
    'profesor_borrar': 'Eliminar profesor',
    # Curso
    'curso_ver':    'Ver cursos',
    'curso_crear':  'Crear curso',
    'curso_editar': 'Editar curso',
    'curso_borrar': 'Eliminar curso',
    # Alumno
    'alumno_ver':    'Ver alumnos',
    'alumno_crear':  'Crear alumno',
    'alumno_editar': 'Editar alumno',
    'alumno_borrar': 'Eliminar alumno',
    # Inscrito
    'inscrito_ver':    'Ver inscritos',
    'inscrito_crear':  'Inscribir alumno',
    'inscrito_editar': 'Editar inscripción',
    'inscrito_borrar': 'Eliminar inscripción',
    # Notas
    'nota_ver':    'Ver notas',
    'nota_crear':  'Registrar nota',
    'nota_editar': 'Editar nota',
    # Pagos
    'pago_ver':    'Ver pagos',
    'pago_crear':  'Registrar pago',
    'pago_editar': 'Editar pago',
    # Admin
    'admin_usuarios':  'Administrar usuarios',
    'admin_roles':     'Administrar roles',
    'admin_permisos':  'Administrar permisos',
}

# Permisos por defecto para cada rol
PERMISOS_POR_ROL = {
    'administrador': list(PERMISOS.keys()),  # Todos los permisos
    'profesor': [
        'gestion_ver', 'grado_ver', 'materia_ver', 'curso_ver',
        'alumno_ver', 'inscrito_ver', 'nota_ver', 'nota_crear', 'nota_editar',
    ],
    'estudiante': [
        'nota_ver', 'pago_ver',
    ],
    'consulta': [
        'gestion_ver', 'grado_ver', 'materia_ver', 'profesor_ver',
        'curso_ver', 'alumno_ver', 'inscrito_ver', 'nota_ver', 'pago_ver',
    ],
    'transcriptor': [
        'gestion_ver', 'grado_ver', 'materia_ver', 'curso_ver',
        'alumno_ver', 'alumno_crear', 'alumno_editar',
        'inscrito_ver', 'inscrito_crear', 'inscrito_editar',
        'nota_ver', 'nota_crear', 'nota_editar',
        'pago_ver', 'pago_crear',
    ],
}
