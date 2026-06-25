from datetime import date
from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from app import db
from app.models import Gestion
from app.decorators import permission_required

gestion_bp = Blueprint('gestion', __name__, url_prefix='/gestion')


@gestion_bp.route('/')
@login_required
@permission_required('gestion_ver')
def index():
    lista = Gestion.query.order_by(Gestion.gestion.desc()).all()
    return render_template('gestion/index.html', gestiones=lista)


@gestion_bp.route('/nueva', methods=['GET', 'POST'])
@login_required
@permission_required('gestion_crear')
def nueva():
    if request.method == 'POST':
        g = Gestion(
            gestion=int(request.form['gestion']),
            plan=request.form['plan'],
            inicio=date.fromisoformat(request.form['inicio']),
            fin=date.fromisoformat(request.form['fin']),
            activo='activo' in request.form,
            creado=date.today(), act=date.today(),
            usu_id=current_user.id
        )
        db.session.add(g)
        db.session.commit()
        flash('Gestión creada exitosamente.', 'success')
        return redirect(url_for('gestion.index'))
    return render_template('gestion/form.html', gestion=None)


@gestion_bp.route('/<int:id>/editar', methods=['GET', 'POST'])
@login_required
@permission_required('gestion_editar')
def editar(id):
    g = Gestion.query.get_or_404(id)
    if request.method == 'POST':
        g.gestion = int(request.form['gestion'])
        g.plan    = request.form['plan']
        g.inicio  = date.fromisoformat(request.form['inicio'])
        g.fin     = date.fromisoformat(request.form['fin'])
        g.activo  = 'activo' in request.form
        g.act     = date.today()
        db.session.commit()
        flash('Gestión actualizada.', 'success')
        return redirect(url_for('gestion.index'))
    return render_template('gestion/form.html', gestion=g)


@gestion_bp.route('/<int:id>/eliminar', methods=['POST'])
@login_required
@permission_required('gestion_borrar')
def eliminar(id):
    g = Gestion.query.get_or_404(id)
    try:
        db.session.delete(g)
        db.session.commit()
        flash('Gestión eliminada.', 'success')
    except Exception:
        db.session.rollback()
        flash('No se puede eliminar: tiene registros relacionados.', 'danger')
    return redirect(url_for('gestion.index'))
