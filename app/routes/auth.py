from datetime import date
from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, login_required, current_user
from app import db, bcrypt
from app.models import Usuario
from app.audit import log_accion

auth_bp = Blueprint('auth', __name__, url_prefix='/auth')


@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard.index'))
    if request.method == 'POST':
        username = request.form.get('usuario', '').strip()
        password = request.form.get('password', '')
        user = Usuario.query.filter_by(usuario=username).first()
        if user and bcrypt.check_password_hash(user.password, password):
            if not user.activo:
                flash('Cuenta desactivada. Contacte al administrador.', 'danger')
                return redirect(url_for('auth.login'))
            user.last_login = date.today()
            db.session.commit()
            login_user(user, remember=request.form.get('remember'))
            log_accion('LOGIN', 'auth', detalle={'usuario': user.usuario, 'email': user.email})
            next_page = request.args.get('next')
            return redirect(next_page or url_for('dashboard.index'))
        log_accion('ERROR', 'auth', status=401, detalle={'usuario_intentado': username, 'motivo': 'credenciales incorrectas'})
        flash('Usuario o contraseña incorrectos.', 'danger')
    return render_template('auth/login.html')


@auth_bp.route('/logout')
@login_required
def logout():
    log_accion('LOGOUT', 'auth', detalle={'usuario': current_user.usuario})
    logout_user()
    flash('Sesión cerrada correctamente.', 'success')
    return redirect(url_for('auth.login'))


@auth_bp.route('/cambiar-password', methods=['GET', 'POST'])
@login_required
def cambiar_password():
    if request.method == 'POST':
        actual = request.form.get('password_actual')
        nueva = request.form.get('password_nueva')
        confirmar = request.form.get('confirmar')
        if not bcrypt.check_password_hash(current_user.password, actual):
            flash('Contraseña actual incorrecta.', 'danger')
        elif nueva != confirmar:
            flash('Las contraseñas no coinciden.', 'danger')
        elif len(nueva) < 6:
            flash('La contraseña debe tener al menos 6 caracteres.', 'danger')
        else:
            current_user.password = bcrypt.generate_password_hash(nueva).decode('utf-8')
            db.session.commit()
            log_accion('UPDATE', 'auth', detalle={'accion': 'cambio_password', 'usuario': current_user.usuario})
            flash('Contraseña actualizada correctamente.', 'success')
            return redirect(url_for('dashboard.index'))
    return render_template('auth/cambiar_password.html')
