from datetime import date
from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from app import db
from app.models import Costo, Curso, Grado
from app.decorators import role_required

costo_bp = Blueprint('costo', __name__, url_prefix='/costo')

NUM_CUOTAS = 10


# ── LISTADO ───────────────────────────────────────────────

@costo_bp.route('/')
@login_required
@role_required('administrador')
def index():
    q      = request.args.get('q', '').strip()
    page   = request.args.get('page', 1, type=int)
    PER_PAGE = 10

    query = Curso.query.join(Grado).order_by(Curso.gestion.desc(), Grado.grado, Curso.paralelo)

    if q:
        query = query.filter(
            db.or_(
                Curso.curso.ilike(f'%{q}%'),
                Curso.paralelo.ilike(f'%{q}%'),
                Grado.grado.ilike(f'%{q}%'),
                db.cast(Curso.gestion, db.String).ilike(f'%{q}%'),
            )
        )

    pagination = query.paginate(page=page, per_page=PER_PAGE, error_out=False)

    # Para cada curso indicar si ya tiene costos asignados
    cursos_info = []
    for curso in pagination.items:
        num_costos = Costo.query.filter_by(cur_id=curso.id).count()
        cursos_info.append({
            'curso': curso,
            'tiene_costos': num_costos == NUM_CUOTAS,
            'num_costos': num_costos,
        })

    return render_template(
        'costo/index.html',
        cursos_info=cursos_info,
        pagination=pagination,
        q=q,
        total=pagination.total,
    )


# ── ASIGNAR / EDITAR COSTOS DE UN CURSO ──────────────────

@costo_bp.route('/<int:cur_id>/asignar', methods=['GET', 'POST'])
@login_required
@role_required('administrador')
def asignar(cur_id):
    curso  = Curso.query.get_or_404(cur_id)
    costos = (Costo.query
              .filter_by(cur_id=cur_id)
              .order_by(Costo.nro_cuota)
              .all())

    # Si no existen las 10 cuotas, crearlas con valores en cero
    if len(costos) < NUM_CUOTAS:
        existentes = {c.nro_cuota for c in costos}
        for nro in range(1, NUM_CUOTAS + 1):
            if nro not in existentes:
                nuevo = Costo(
                    cur_id=cur_id,
                    nro_cuota=nro,
                    cuota=0,
                    obs='',
                    creado=date.today(),
                    act=date.today(),
                    usu_id=current_user.id,
                )
                db.session.add(nuevo)
        db.session.commit()
        costos = (Costo.query
                  .filter_by(cur_id=cur_id)
                  .order_by(Costo.nro_cuota)
                  .all())

    if request.method == 'POST':
        try:
            for costo in costos:
                campo_cuota = f'cuota_{costo.nro_cuota}'
                campo_obs   = f'obs_{costo.nro_cuota}'
                valor_cuota = request.form.get(campo_cuota, '0').strip() or '0'
                costo.cuota  = float(valor_cuota)
                costo.obs    = request.form.get(campo_obs, '').strip()
                costo.act    = date.today()
                costo.usu_id = current_user.id
            db.session.commit()
            flash('Costos asignados correctamente.', 'success')
            return redirect(url_for('costo.index'))
        except (ValueError, TypeError):
            db.session.rollback()
            flash('Error: verifique que los montos sean valores numéricos válidos.', 'danger')

    return render_template('costo/form.html', curso=curso, costos=costos)
