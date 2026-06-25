from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify
from flask_login import login_required, current_user
from app import db
from app.models import Alumno, Inscrito, Pago
from app.decorators import role_required

anulacion_bp = Blueprint('anulacion', __name__, url_prefix='/anulacion')


# ── Búsqueda AJAX de alumnos (reutiliza misma lógica que pago) ────────────────

@anulacion_bp.route('/buscar-alumno')
@login_required
@role_required('administrador')
def buscar_alumno():
    q = request.args.get('q', '').strip()
    if not q or len(q) < 2:
        return jsonify([])
    resultados = Alumno.query.filter(
        db.or_(
            Alumno.nombre.ilike(f'%{q}%'),
            Alumno.paterno.ilike(f'%{q}%'),
            Alumno.materno.ilike(f'%{q}%'),
            db.cast(Alumno.ci, db.String).ilike(f'%{q}%'),
        )
    ).order_by(Alumno.paterno, Alumno.nombre).limit(10).all()
    return jsonify([{
        'id': a.id,
        'texto': a.nombre_completo,
        'ci': str(a.ci) if a.ci else '—',
        'activo': a.activo,
    } for a in resultados])


# ── Pantalla principal ────────────────────────────────────────────────────────

@anulacion_bp.route('/', methods=['GET'])
@login_required
@role_required('administrador')
def index():
    """Muestra el formulario con las dos opciones de anulación."""
    alu_id       = request.args.get('alu_id', type=int)
    alumno_sel   = None
    pagos_alumno = []
    pagos_todos  = None   # None = no previsualizado aún

    if alu_id:
        alumno_sel = Alumno.query.get_or_404(alu_id)
        ins = Inscrito.query.filter_by(alu_id=alu_id).first()
        if ins:
            pagos_alumno = (Pago.query
                            .filter_by(ins_id=ins.id, pagado=False)
                            .order_by(Pago.nro_cuota)
                            .all())

    # Previsualización "anular todos": cuenta cuotas no pagadas globalmente
    total_no_pagados = Pago.query.filter_by(pagado=False).count()

    return render_template(
        'anulacion/index.html',
        alu_id=alu_id,
        alumno_sel=alumno_sel,
        pagos_alumno=pagos_alumno,
        total_no_pagados=total_no_pagados,
    )


# ── Anular plan de UN alumno ──────────────────────────────────────────────────

@anulacion_bp.route('/alumno', methods=['POST'])
@login_required
@role_required('administrador')
def anular_alumno():
    alu_id = request.form.get('alu_id', type=int)
    if not alu_id:
        flash('Debe seleccionar un alumno.', 'danger')
        return redirect(url_for('anulacion.index'))

    alumno = Alumno.query.get_or_404(alu_id)
    ins = Inscrito.query.filter_by(alu_id=alu_id).first()

    if not ins:
        flash(f'El alumno {alumno.nombre_completo} no tiene inscripción registrada.', 'danger')
        return redirect(url_for('anulacion.index'))

    # Eliminar solo cuotas no pagadas
    eliminados = (Pago.query
                  .filter_by(ins_id=ins.id, pagado=False)
                  .all())

    if not eliminados:
        flash(
            f'{alumno.nombre_completo} no tiene cuotas pendientes de pago para anular.',
            'warning'
        )
        return redirect(url_for('anulacion.index', alu_id=alu_id))

    cantidad = len(eliminados)
    for p in eliminados:
        db.session.delete(p)
    db.session.commit()

    flash(
        f'Plan de pagos anulado: se eliminaron {cantidad} cuota(s) no pagada(s) '
        f'de {alumno.nombre_completo}.',
        'success'
    )
    return redirect(url_for('anulacion.index'))


# ── Anular plan de TODOS los alumnos ─────────────────────────────────────────

@anulacion_bp.route('/todos', methods=['POST'])
@login_required
@role_required('administrador')
def anular_todos():
    confirmacion = request.form.get('confirmar', '').strip()
    if confirmacion != 'ANULAR':
        flash('Confirmación incorrecta. Escriba ANULAR para continuar.', 'danger')
        return redirect(url_for('anulacion.index'))

    # Eliminar todas las cuotas con pagado=False
    pendientes = Pago.query.filter_by(pagado=False).all()

    if not pendientes:
        flash('No existen cuotas pendientes de pago para anular.', 'warning')
        return redirect(url_for('anulacion.index'))

    cantidad = len(pendientes)
    for p in pendientes:
        db.session.delete(p)
    db.session.commit()

    flash(
        f'Anulación masiva completada: se eliminaron {cantidad} cuota(s) '
        f'no pagada(s) de todos los alumnos.',
        'success'
    )
    return redirect(url_for('anulacion.index'))
