from datetime import date
from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify
from flask_login import login_required, current_user
from app import db, bcrypt
from app.models import Usuario, Rol, Permiso, Profesor, usuario_rol, rol_permiso
from app.decorators import role_required, PERMISOS, PERMISOS_POR_ROL

admin_bp = Blueprint('admin', __name__, url_prefix='/admin')


# ── Usuarios ──────────────────────────────────────────────

@admin_bp.route('/usuarios')
@login_required
@role_required('administrador')
def usuarios():
    lista = Usuario.query.order_by(Usuario.usuario).all()
    return render_template('admin/usuarios.html', usuarios=lista)


@admin_bp.route('/usuarios/nuevo', methods=['GET', 'POST'])
@login_required
@role_required('administrador')
def usuario_nuevo():
    roles = Rol.query.all()
    if request.method == 'POST':
        usu = request.form.get('usuario', '').strip()
        email = request.form.get('email', '').strip()
        pwd = request.form.get('password', '')
        roles_sel = request.form.getlist('roles')
        if Usuario.query.filter_by(usuario=usu).first():
            flash('El nombre de usuario ya existe.', 'danger')
        else:
            hashed = bcrypt.generate_password_hash(pwd).decode('utf-8')
            nuevo = Usuario(usuario=usu, email=email, password=hashed,
                            activo=True, last_login=date.today())
            db.session.add(nuevo)
            db.session.flush()
            for rid in roles_sel:
                rol = Rol.query.get(int(rid))
                if rol:
                    nuevo.roles.append(rol)
            db.session.commit()
            flash('Usuario creado exitosamente.', 'success')
            if request.headers.get('HX-Request'):
                return '', 200
            return redirect(url_for('admin.usuarios'))
    return render_template('admin/usuario_form.html', usuario=None, roles=roles)


@admin_bp.route('/usuarios/<int:id>/editar', methods=['GET', 'POST'])
@login_required
@role_required('administrador')
def usuario_editar(id):
    u = Usuario.query.get_or_404(id)
    roles = Rol.query.all()
    if request.method == 'POST':
        u.email = request.form.get('email', '').strip()
        u.activo = 'activo' in request.form
        roles_sel = request.form.getlist('roles')
        u.roles = []
        for rid in roles_sel:
            rol = Rol.query.get(int(rid))
            if rol:
                u.roles.append(rol)
        pwd = request.form.get('password', '')
        if pwd:
            u.password = bcrypt.generate_password_hash(pwd).decode('utf-8')
        db.session.commit()
        flash('Usuario actualizado.', 'success')
        return redirect(url_for('admin.usuarios'))
    return render_template('admin/usuario_form.html', usuario=u, roles=roles)


@admin_bp.route('/usuarios/<int:id>/eliminar', methods=['DELETE', 'POST'])
@login_required
@role_required('administrador')
def usuario_eliminar(id):
    u = Usuario.query.get_or_404(id)
    if u.id == current_user.id:
        flash('No puede eliminar su propio usuario.', 'danger')
        return redirect(url_for('admin.usuarios'))
    db.session.delete(u)
    db.session.commit()
    flash('Usuario eliminado.', 'success')
    return redirect(url_for('admin.usuarios'))


# ── Roles ─────────────────────────────────────────────────

@admin_bp.route('/roles')
@login_required
@role_required('administrador')
def roles():
    lista = Rol.query.order_by(Rol.rol).all()
    return render_template('admin/roles.html', roles=lista)


@admin_bp.route('/roles/nuevo', methods=['GET', 'POST'])
@login_required
@role_required('administrador')
def rol_nuevo():
    permisos = Permiso.query.all()
    if request.method == 'POST':
        nombre = request.form.get('rol', '').strip()
        desc   = request.form.get('descripcion', '').strip()
        perms  = request.form.getlist('permisos')
        if Rol.query.filter_by(rol=nombre).first():
            flash('El rol ya existe.', 'danger')
        else:
            nuevo = Rol(rol=nombre, descripcion=desc)
            db.session.add(nuevo)
            db.session.flush()
            for pid in perms:
                p = Permiso.query.get(int(pid))
                if p:
                    nuevo.permisos.append(p)
            db.session.commit()
            flash('Rol creado exitosamente.', 'success')
            return redirect(url_for('admin.roles'))
    return render_template('admin/rol_form.html', rol=None, permisos=permisos)


@admin_bp.route('/roles/<int:id>/editar', methods=['GET', 'POST'])
@login_required
@role_required('administrador')
def rol_editar(id):
    r = Rol.query.get_or_404(id)
    permisos = Permiso.query.all()
    if request.method == 'POST':
        r.rol         = request.form.get('rol', '').strip()
        r.descripcion = request.form.get('descripcion', '').strip()
        perms = request.form.getlist('permisos')
        r.permisos = []
        for pid in perms:
            p = Permiso.query.get(int(pid))
            if p:
                r.permisos.append(p)
        r.act = date.today()
        db.session.commit()
        flash('Rol actualizado.', 'success')
        return redirect(url_for('admin.roles'))
    return render_template('admin/rol_form.html', rol=r, permisos=permisos)


# ── Permisos ──────────────────────────────────────────────

@admin_bp.route('/permisos')
@login_required
@role_required('administrador')
def permisos():
    lista = Permiso.query.order_by(Permiso.permiso).all()
    return render_template('admin/permisos.html', permisos=lista)


# ── Asignar Usuario → Profesor ────────────────────────────

@admin_bp.route('/asignar-profesor', methods=['GET', 'POST'])
@login_required
@role_required('administrador')
def asignar_profesor():
    profesores = (Profesor.query
                  .order_by(Profesor.paterno, Profesor.nombre)
                  .all())
    # Usuarios con rol 'profesor' que aún no están vinculados
    usuarios = (Usuario.query
                .join(Usuario.roles)
                .filter(Rol.rol == 'profesor')
                .order_by(Usuario.usuario)
                .all())

    if request.method == 'POST':
        pro_id = request.form.get('pro_id', type=int)
        usu_id = request.form.get('usu_id', type=int)

        if not pro_id or not usu_id:
            flash('Debe seleccionar un profesor y un usuario.', 'danger')
            return redirect(url_for('admin.asignar_profesor'))

        profesor = Profesor.query.get_or_404(pro_id)
        usuario  = Usuario.query.get_or_404(usu_id)

        # Verificar que el usuario no esté ya asignado a otro profesor
        conflicto = Profesor.query.filter(
            Profesor.usr_id_login == usu_id,
            Profesor.id != pro_id
        ).first()
        if conflicto:
            flash(
                f'El usuario "{usuario.usuario}" ya está asignado al profesor '
                f'"{conflicto.nombre_completo}". Desvincúlelo primero.',
                'danger'
            )
            return redirect(url_for('admin.asignar_profesor'))

        profesor.usr_id_login = usu_id
        db.session.commit()
        flash(
            f'Usuario "{usuario.usuario}" asignado correctamente al profesor '
            f'"{profesor.nombre_completo}".',
            'success'
        )
        return redirect(url_for('admin.asignar_profesor'))

    return render_template('admin/asignar_profesor.html',
                           profesores=profesores,
                           usuarios=usuarios)


@admin_bp.route('/asignar-profesor/desvincular/<int:pro_id>', methods=['POST'])
@login_required
@role_required('administrador')
def desvincular_profesor(pro_id):
    profesor = Profesor.query.get_or_404(pro_id)
    profesor.usr_id_login = None
    db.session.commit()
    flash(f'Usuario desvinculado del profesor "{profesor.nombre_completo}".', 'success')
    return redirect(url_for('admin.asignar_profesor'))
