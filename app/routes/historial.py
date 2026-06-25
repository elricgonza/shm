from datetime import datetime, date, timedelta

from flask import Blueprint, render_template, request, abort
from flask_login import login_required, current_user

from app import db
from app.models import AuditLog, Usuario

historial_bp = Blueprint('historial', __name__, url_prefix='/historial')

PER_PAGE = 25


@historial_bp.route('/')
@login_required
def index():
    """Visor de historial de auditoría — solo administrador."""
    if not current_user.has_role('administrador'):
        abort(403)

    # ── Filtros ──────────────────────────────────────────────────────────────
    usu_id  = request.args.get('usu_id',  type=int)
    accion  = request.args.get('accion',  '').strip()
    modulo  = request.args.get('modulo',  '').strip()
    fecha_d = request.args.get('fecha_d', '').strip()   # desde
    fecha_h = request.args.get('fecha_h', '').strip()   # hasta
    q       = request.args.get('q',       '').strip()   # búsqueda libre en detalle
    page    = request.args.get('page', 1, type=int)

    query = AuditLog.query

    if usu_id:
        query = query.filter(AuditLog.usu_id == usu_id)
    if accion:
        query = query.filter(AuditLog.accion == accion)
    if modulo:
        query = query.filter(AuditLog.modulo == modulo)
    if fecha_d:
        try:
            query = query.filter(AuditLog.creado >= datetime.fromisoformat(fecha_d))
        except ValueError:
            pass
    if fecha_h:
        try:
            dt_h = datetime.fromisoformat(fecha_h) + timedelta(days=1)
            query = query.filter(AuditLog.creado < dt_h)
        except ValueError:
            pass
    if q:
        query = query.filter(AuditLog.detalle.ilike(f'%{q}%'))

    query = query.order_by(AuditLog.creado.desc())
    pagination = query.paginate(page=page, per_page=PER_PAGE, error_out=False)

    # Valores para los selectores de filtro
    usuarios  = (db.session.query(AuditLog.usu_id, AuditLog.usuario)
                 .distinct()
                 .filter(AuditLog.usu_id.isnot(None))
                 .order_by(AuditLog.usuario)
                 .all())
    acciones  = (db.session.query(AuditLog.accion)
                 .distinct()
                 .order_by(AuditLog.accion)
                 .all())
    modulos   = (db.session.query(AuditLog.modulo)
                 .distinct()
                 .order_by(AuditLog.modulo)
                 .all())

    return render_template(
        'historial/index.html',
        logs=pagination.items,
        pagination=pagination,
        usuarios=[{'id': u.usu_id, 'nombre': u.usuario} for u in usuarios],
        acciones=[a.accion for a in acciones],
        modulos=[m.modulo for m in modulos],
        # filtros activos (para repoblar el form)
        f_usu_id  = usu_id,
        f_accion  = accion,
        f_modulo  = modulo,
        f_fecha_d = fecha_d,
        f_fecha_h = fecha_h,
        f_q       = q,
    )
