from datetime import date
from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from app import db
from app.models import Asignado, Curso, Materia, Grado, Profesor
from app.decorators import role_required

asignado_bp = Blueprint('asignado', __name__, url_prefix='/asignado')


# ── Helpers ───────────────────────────────────────────────

def _pares_existentes():
    """Retorna un set de (cur_id, mat_id) ya presentes en ASIGNADO."""
    rows = db.session.query(Asignado.cur_id, Asignado.mat_id).all()
    return {(r.cur_id, r.mat_id) for r in rows}


# ── Index: lista completa de asignaciones ─────────────────

@asignado_bp.route('/')
@login_required
@role_required('administrador')
def index():
    cur_id = request.args.get('cur_id', type=int)
    page   = request.args.get('page', 1, type=int)

    query = (Asignado.query
             .join(Curso, Asignado.cur_id == Curso.id)
             .join(Grado, Curso.gra_id == Grado.id)
             .join(Materia, Asignado.mat_id == Materia.id)
             .outerjoin(Profesor, Asignado.pro_id == Profesor.id))

    if cur_id:
        query = query.filter(Asignado.cur_id == cur_id)

    query = query.order_by(Curso.gestion.desc(), Grado.grado, Curso.paralelo, Materia.materia)
    pagination = query.paginate(page=page, per_page=20, error_out=False)

    cursos = (Curso.query
              .join(Grado, Curso.gra_id == Grado.id)
              .order_by(Curso.gestion.desc(), Grado.grado, Curso.paralelo)
              .all())

    # Contadores para el encabezado
    total      = Asignado.query.count()
    sin_profe  = Asignado.query.filter(Asignado.pro_id == None).count()

    return render_template('asignado/index.html',
                           asignados=pagination.items,
                           pagination=pagination,
                           cursos=cursos,
                           cur_id=cur_id,
                           total=total,
                           sin_profe=sin_profe)


@asignado_bp.route('/<int:id>/eliminar', methods=['POST'])
@login_required
@role_required('administrador')
def eliminar(id):
    a = Asignado.query.get_or_404(id)
    try:
        db.session.delete(a)
        db.session.commit()
        flash('Registro eliminado.', 'success')
    except Exception:
        db.session.rollback()
        flash('No se puede eliminar: tiene registros relacionados.', 'danger')
    return redirect(url_for('asignado.index'))


# ── Parte 1: Poblar ASIGNADO (cur_id + mat_id) ────────────

@asignado_bp.route('/poblar', methods=['GET', 'POST'])
@login_required
@role_required('administrador')
def poblar():
    """
    Genera registros en ASIGNADO para cada CURSO con las MATERIAS
    correspondientes a su grado (curso.gra_id == materia.gra_id).
    El pro_id queda NULL pendiente de asignación posterior.
    No duplica pares (cur_id, mat_id) ya existentes.
    """
    # Todos los cursos con su grado y el conteo de materias disponibles
    cursos = (Curso.query
              .join(Grado, Curso.gra_id == Grado.id)
              .order_by(Curso.gestion.desc(), Grado.grado, Curso.paralelo)
              .all())

    # Para cada curso: cuántas materias tiene su grado y cuántas ya están asignadas
    existentes = _pares_existentes()

    resumen_cursos = []
    for c in cursos:
        materias_grado = Materia.query.filter_by(gra_id=c.gra_id).count()
        ya_asignadas   = sum(1 for (ci, mi) in existentes if ci == c.id)
        pendientes     = materias_grado - ya_asignadas
        resumen_cursos.append({
            'curso':          c,
            'materias_grado': materias_grado,
            'ya_asignadas':   ya_asignadas,
            'pendientes':     pendientes,
        })

    if request.method == 'POST':
        cur_ids_sel = request.form.getlist('cur_ids', type=int)

        if not cur_ids_sel:
            flash('Seleccione al menos un curso.', 'warning')
            return redirect(url_for('asignado.poblar'))

        existentes = _pares_existentes()   # Refrescar al momento del POST
        creados = 0
        omitidos = 0

        for cur_id in cur_ids_sel:
            curso = Curso.query.get(cur_id)
            if not curso:
                continue
            materias = Materia.query.filter_by(gra_id=curso.gra_id).all()
            for mat in materias:
                if (cur_id, mat.id) in existentes:
                    omitidos += 1
                    continue
                nuevo = Asignado(
                    cur_id=cur_id,
                    mat_id=mat.id,
                    pro_id=None,          # se completa en Parte 2
                    creado=date.today(),
                    act=date.today(),
                    usu_id=current_user.id,
                )
                db.session.add(nuevo)
                existentes.add((cur_id, mat.id))
                creados += 1

        db.session.commit()

        if creados:
            flash(f'{creados} registro(s) generado(s) en ASIGNADO.', 'success')
        if omitidos:
            flash(f'{omitidos} par(es) ya existían y fueron omitidos.', 'info')
        if not creados and not omitidos:
            flash('No se generaron registros (sin materias en los grados seleccionados).', 'warning')

        return redirect(url_for('asignado.poblar'))

    return render_template('asignado/poblar.html', resumen_cursos=resumen_cursos)


# ── Parte 2: Asignar Profesor a registros sin pro_id ──────

@asignado_bp.route('/asignar-profesor', methods=['GET', 'POST'])
@login_required
@role_required('administrador')
def asignar_profesor():
    """
    Complementa los registros de ASIGNADO que tienen pro_id = NULL
    asignando un PROFESOR a uno o varios registros por curso.
    También permite cambiar el profesor en registros ya asignados.
    """
    # Registros pendientes (sin profesor), agrupados por curso
    sin_asignar = (Asignado.query
                   .filter(Asignado.pro_id == None)
                   .join(Curso, Asignado.cur_id == Curso.id)
                   .join(Grado, Curso.gra_id == Grado.id)
                   .join(Materia, Asignado.mat_id == Materia.id)
                   .order_by(Curso.gestion.desc(), Grado.grado, Curso.paralelo, Materia.materia)
                   .all())

    # Agrupar por curso para presentación
    grupos = {}
    for a in sin_asignar:
        key = a.cur_id
        if key not in grupos:
            grupos[key] = {'curso': a.curso, 'asignados': []}
        grupos[key]['asignados'].append(a)

    profesores = (Profesor.query
                  .filter_by(activo=True)
                  .order_by(Profesor.paterno, Profesor.nombre)
                  .all())

    if request.method == 'POST':
        # El formulario envía pares: asig_<id>=<pro_id> para cada registro
        actualizados = 0
        errores = 0

        for key, value in request.form.items():
            if not key.startswith('asig_'):
                continue
            try:
                asig_id = int(key[5:])
                pro_id  = int(value) if value else None
            except (ValueError, TypeError):
                continue

            if pro_id is None:
                continue   # No se seleccionó profesor para este registro

            asig = Asignado.query.get(asig_id)
            if not asig:
                continue

            # Verificar que el profesor existe
            if not Profesor.query.get(pro_id):
                errores += 1
                continue

            asig.pro_id = pro_id
            asig.act    = date.today()
            asig.usu_id = current_user.id
            actualizados += 1

        db.session.commit()

        if actualizados:
            flash(f'{actualizados} asignación(es) de profesor guardada(s).', 'success')
        if errores:
            flash(f'{errores} registro(s) con error (profesor no encontrado).', 'danger')
        if not actualizados and not errores:
            flash('No se realizaron cambios.', 'info')

        return redirect(url_for('asignado.asignar_profesor'))

    return render_template('asignado/asignar_profesor.html',
                           grupos=grupos,
                           profesores=profesores,
                           total_pendientes=len(sin_asignar))
