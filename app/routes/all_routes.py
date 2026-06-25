from datetime import date, datetime
from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify
from flask_login import login_required, current_user
from app import db
from app.models import Grado, Gestion, Materia, Profesor, Curso, Alumno, Inscrito, Asignado, Nota, Pago, Costo
from app.decorators import permission_required
from app.audit import log_accion
from flask import abort
PER_PAGE = 10   # Registros por página en todas las listas

# ── GRADO ─────────────────────────────────────────────────
grado_bp = Blueprint('grado', __name__, url_prefix='/grado')

@grado_bp.route('/')
@login_required
@permission_required('grado_ver')
def index():
    q      = request.args.get('q', '').strip()
    ges_id = request.args.get('ges_id', type=int)
    nivel  = request.args.get('nivel', '').strip()
    page   = request.args.get('page', 1, type=int)

    query = Grado.query.join(Gestion)

    if q:
        query = query.filter(Grado.grado.ilike(f'%{q}%'))
    if ges_id:
        query = query.filter(Grado.ges_id == ges_id)
    if nivel:
        query = query.filter(Grado.nivel.ilike(f'%{nivel}%'))

    query = query.order_by(Gestion.gestion.desc(), Grado.nivel, Grado.grado)
    pagination = query.paginate(page=page, per_page=PER_PAGE, error_out=False)

    gestiones = Gestion.query.order_by(Gestion.gestion.desc()).all()
    niveles   = [r[0] for r in db.session.query(Grado.nivel).distinct().order_by(Grado.nivel).all()]

    return render_template('grado/index.html',
        grados=pagination.items, pagination=pagination,
        q=q, ges_id=ges_id, nivel=nivel,
        gestiones=gestiones, niveles=niveles)

@grado_bp.route('/nuevo', methods=['GET', 'POST'])
@login_required
@permission_required('grado_crear')
def nuevo():
    gestiones = Gestion.query.order_by(Gestion.gestion.desc()).all()
    if request.method == 'POST':
        g = Grado(
            grado=request.form['grado'], nivel=request.form['nivel'],
            ges_id=int(request.form['ges_id']),
            creado=datetime.now(), act=datetime.now(), usu_id=current_user.id
        )
        db.session.add(g); db.session.commit()
        log_accion('CREATE', 'grado', entidad_id=g.id, detalle={'grado': g.grado, 'nivel': g.nivel})
        flash('Grado creado.', 'success')
        return redirect(url_for('grado.index'))
    return render_template('grado/form.html', grado=None, gestiones=gestiones)

@grado_bp.route('/<int:id>/editar', methods=['GET', 'POST'])
@login_required
@permission_required('grado_editar')
def editar(id):
    g = Grado.query.get_or_404(id)
    gestiones = Gestion.query.order_by(Gestion.gestion.desc()).all()
    if request.method == 'POST':
        g.grado = request.form['grado']; g.nivel = request.form['nivel']
        g.ges_id = int(request.form['ges_id']); g.act = datetime.now()
        db.session.commit()
        log_accion('UPDATE', 'grado', entidad_id=g.id, detalle={'grado': g.grado, 'nivel': g.nivel})
        flash('Grado actualizado.', 'success')
        return redirect(url_for('grado.index'))
    return render_template('grado/form.html', grado=g, gestiones=gestiones)

@grado_bp.route('/<int:id>/eliminar', methods=['POST'])
@login_required
@permission_required('grado_borrar')
def eliminar(id):
    g = Grado.query.get_or_404(id)
    try:
        db.session.delete(g); db.session.commit()
        log_accion('DELETE', 'grado', entidad_id=g.id, detalle={'grado': g.grado})
        flash('Grado eliminado.', 'success')
    except Exception:
        db.session.rollback(); flash('No se puede eliminar: tiene registros relacionados.', 'danger')
    return redirect(url_for('grado.index'))


# ── MATERIA ───────────────────────────────────────────────
materia_bp = Blueprint('materia', __name__, url_prefix='/materia')

@materia_bp.route('/')
@login_required
@permission_required('materia_ver')
def index():
    q      = request.args.get('q', '').strip()
    gra_id = request.args.get('gra_id', type=int)
    page   = request.args.get('page', 1, type=int)

    query = Materia.query.join(Grado)

    if q:
        query = query.filter(Materia.materia.ilike(f'%{q}%'))
    if gra_id:
        query = query.filter(Materia.gra_id == gra_id)

    query = query.order_by(Grado.grado, Materia.materia)
    pagination = query.paginate(page=page, per_page=PER_PAGE, error_out=False)

    grados = Grado.query.order_by(Grado.grado).all()

    return render_template('materia/index.html',
        materias=pagination.items, pagination=pagination,
        q=q, gra_id=gra_id, grados=grados)

@materia_bp.route('/nueva', methods=['GET', 'POST'])
@login_required
@permission_required('materia_crear')
def nueva():
    grados = Grado.query.order_by(Grado.grado).all()
    if request.method == 'POST':
        m = Materia(
            materia=request.form['materia'], gra_id=int(request.form['gra_id']),
            creado=datetime.now(), act=datetime.now(), usu_id=current_user.id
        )
        db.session.add(m); db.session.commit()
        log_accion('CREATE', 'materia', entidad_id=m.id, detalle={'materia': m.materia})
        flash('Materia creada.', 'success')
        return redirect(url_for('materia.index'))
    return render_template('materia/form.html', materia=None, grados=grados)

@materia_bp.route('/<int:id>/editar', methods=['GET', 'POST'])
@login_required
@permission_required('materia_editar')
def editar(id):
    m = Materia.query.get_or_404(id)
    grados = Grado.query.order_by(Grado.grado).all()
    if request.method == 'POST':
        m.materia = request.form['materia']; m.gra_id = int(request.form['gra_id'])
        m.act = datetime.now(); db.session.commit()
        log_accion('UPDATE', 'materia', entidad_id=m.id, detalle={'materia': m.materia})
        flash('Materia actualizada.', 'success')
        return redirect(url_for('materia.index'))
    return render_template('materia/form.html', materia=m, grados=grados)

@materia_bp.route('/<int:id>/eliminar', methods=['POST'])
@login_required
@permission_required('materia_borrar')
def eliminar(id):
    m = Materia.query.get_or_404(id)
    try:
        db.session.delete(m); db.session.commit()
        log_accion('DELETE', 'materia', entidad_id=m.id, detalle={'materia': m.materia})
        flash('Materia eliminada.', 'success')
    except Exception:
        db.session.rollback(); flash('No se puede eliminar: tiene registros relacionados.', 'danger')
    return redirect(url_for('materia.index'))


# ── PROFESOR ──────────────────────────────────────────────
profesor_bp = Blueprint('profesor', __name__, url_prefix='/profesor')

@profesor_bp.route('/')
@login_required
@permission_required('profesor_ver')
def index():
    q      = request.args.get('q', '').strip()
    activo = request.args.get('activo', '')      # 'true' | 'false' | ''
    page   = request.args.get('page', 1, type=int)

    query = Profesor.query

    if q:
        query = query.filter(
            db.or_(
                Profesor.nombre.ilike(f'%{q}%'),
                Profesor.paterno.ilike(f'%{q}%'),
                Profesor.materno.ilike(f'%{q}%'),
                Profesor.formacion.ilike(f'%{q}%'),
            )
        )
    if activo == 'true':
        query = query.filter(Profesor.activo == True)
    elif activo == 'false':
        query = query.filter(Profesor.activo == False)

    query = query.order_by(Profesor.paterno, Profesor.nombre)
    pagination = query.paginate(page=page, per_page=PER_PAGE, error_out=False)

    return render_template('profesor/index.html',
        profesores=pagination.items, pagination=pagination,
        q=q, activo=activo)

@profesor_bp.route('/nuevo', methods=['GET', 'POST'])
@login_required
@permission_required('profesor_crear')
def nuevo():
    if request.method == 'POST':
        p = Profesor(
            nombre=request.form['nombre'], paterno=request.form.get('paterno'),
            materno=request.form.get('materno'),
            masculino=request.form.get('genero') == 'M',
            ci=request.form.get('ci') or None,
            formacion=request.form.get('formacion'),
            email=request.form.get('email'),
            activo='activo' in request.form,
            creado=datetime.now(), act=datetime.now(), usu_id=current_user.id
        )
        db.session.add(p); db.session.commit()
        log_accion('CREATE', 'profesor', entidad_id=p.id, detalle={'nombre': p.nombre_completo, 'ci': p.ci})
        flash('Profesor registrado.', 'success')
        return redirect(url_for('profesor.index'))
    return render_template('profesor/form.html', profesor=None)

@profesor_bp.route('/<int:id>/editar', methods=['GET', 'POST'])
@login_required
@permission_required('profesor_editar')
def editar(id):
    p = Profesor.query.get_or_404(id)
    if request.method == 'POST':
        p.nombre = request.form['nombre']; p.paterno = request.form.get('paterno')
        p.materno = request.form.get('materno')
        p.masculino = request.form.get('genero') == 'M'
        p.ci = request.form.get('ci') or None
        p.formacion = request.form.get('formacion'); p.email = request.form.get('email')
        p.activo = 'activo' in request.form; p.act = datetime.now()
        db.session.commit()
        log_accion('UPDATE', 'profesor', entidad_id=p.id, detalle={'nombre': p.nombre_completo, 'activo': p.activo})
        flash('Profesor actualizado.', 'success')
        return redirect(url_for('profesor.index'))
    return render_template('profesor/form.html', profesor=p)

@profesor_bp.route('/<int:id>/eliminar', methods=['POST'])
@login_required
@permission_required('profesor_borrar')
def eliminar(id):
    p = Profesor.query.get_or_404(id)
    try:
        db.session.delete(p); db.session.commit()
        log_accion('DELETE', 'profesor', entidad_id=p.id, detalle={'nombre': p.nombre_completo})
        flash('Profesor eliminado.', 'success')
    except Exception:
        db.session.rollback(); flash('No se puede eliminar: tiene asignaciones.', 'danger')
    return redirect(url_for('profesor.index'))


# ── CURSO ─────────────────────────────────────────────────
curso_bp = Blueprint('curso', __name__, url_prefix='/curso')

@curso_bp.route('/')
@login_required
@permission_required('curso_ver')
def index():
    q    = request.args.get('q', '').strip()
    page = request.args.get('page', 1, type=int)
    query = Curso.query.join(Grado).order_by(Curso.gestion.desc(), Grado.grado, Curso.paralelo)
    if q:
        query = query.filter(
            db.or_(
                Curso.curso.ilike(f'%{q}%'),
                Curso.paralelo.ilike(f'%{q}%'),
                Curso.aula.ilike(f'%{q}%'),
                Grado.grado.ilike(f'%{q}%'),
                db.cast(Curso.gestion, db.String).ilike(f'%{q}%'),
            )
        )
    pagination = query.paginate(page=page, per_page=PER_PAGE, error_out=False)
    return render_template('curso/index.html', cursos=pagination.items,
                           pagination=pagination, q=q, total=pagination.total)

@curso_bp.route('/nuevo', methods=['GET', 'POST'])
@login_required
@permission_required('curso_crear')
def nuevo():
    grados = Grado.query.order_by(Grado.grado).all()
    if request.method == 'POST':
        c = Curso(
            curso=request.form.get('curso'), paralelo=request.form['paralelo'],
            gra_id=int(request.form['gra_id']), aula=request.form.get('aula'),
            capacidad=request.form.get('capacidad') or None,
            gestion=int(request.form['gestion']),
            creado=datetime.now(), act=datetime.now(), usu_id=current_user.id
        )
        db.session.add(c); db.session.commit()
        flash('Curso creado.', 'success')
        return redirect(url_for('curso.index'))
    return render_template('curso/form.html', curso=None, grados=grados)

@curso_bp.route('/<int:id>/editar', methods=['GET', 'POST'])
@login_required
@permission_required('curso_editar')
def editar(id):
    c = Curso.query.get_or_404(id)
    grados = Grado.query.order_by(Grado.grado).all()
    if request.method == 'POST':
        c.curso = request.form.get('curso'); c.paralelo = request.form['paralelo']
        c.gra_id = int(request.form['gra_id']); c.aula = request.form.get('aula')
        c.capacidad = request.form.get('capacidad') or None
        c.gestion = int(request.form['gestion']); c.act = datetime.now()
        db.session.commit(); flash('Curso actualizado.', 'success')
        return redirect(url_for('curso.index'))
    return render_template('curso/form.html', curso=c, grados=grados)

@curso_bp.route('/<int:id>/eliminar', methods=['POST'])
@login_required
@permission_required('curso_borrar')
def eliminar(id):
    c = Curso.query.get_or_404(id)
    try:
        db.session.delete(c); db.session.commit(); flash('Curso eliminado.', 'success')
    except Exception:
        db.session.rollback(); flash('No se puede eliminar: tiene registros relacionados.', 'danger')
    return redirect(url_for('curso.index'))


# ── ALUMNO ────────────────────────────────────────────────
alumno_bp = Blueprint('alumno', __name__, url_prefix='/alumno')

@alumno_bp.route('/')
@login_required
@permission_required('alumno_ver')
def index():
    q    = request.args.get('q', '').strip()
    page = request.args.get('page', 1, type=int)
    query = Alumno.query
    if q:
        query = query.filter(
            db.or_(Alumno.nombre.ilike(f'%{q}%'),
                   Alumno.paterno.ilike(f'%{q}%'),
                   Alumno.materno.ilike(f'%{q}%'),
                   db.cast(Alumno.ci, db.String).ilike(f'%{q}%'))
        )
    query = query.order_by(Alumno.paterno, Alumno.nombre)
    pagination = query.paginate(page=page, per_page=PER_PAGE, error_out=False)
    return render_template('alumno/index.html', alumnos=pagination.items, pagination=pagination, q=q, total=pagination.total)

@alumno_bp.route('/nuevo', methods=['GET', 'POST'])
@login_required
@permission_required('alumno_crear')
def nuevo():
    if request.method == 'POST':
        a = Alumno(
            nombre=request.form['nombre'], paterno=request.form.get('paterno'),
            materno=request.form.get('materno'),
            nacimiento=date.fromisoformat(request.form['nacimiento']) if request.form.get('nacimiento') else None,
            masculino=request.form.get('genero') == 'M',
            ci=request.form.get('ci') or None,
            direccion=request.form.get('direccion'), email=request.form.get('email'),
            activo='activo' in request.form, obs=request.form.get('obs'),
            creado=datetime.now(), act=datetime.now(), usu_id=current_user.id
        )
        db.session.add(a); db.session.commit()
        log_accion('CREATE', 'alumno', entidad_id=a.id, detalle={'nombre': a.nombre_completo, 'ci': a.ci})
        flash('Alumno registrado.', 'success')
        return redirect(url_for('alumno.index'))
    return render_template('alumno/form.html', alumno=None)

@alumno_bp.route('/<int:id>/editar', methods=['GET', 'POST'])
@login_required
@permission_required('alumno_editar')
def editar(id):
    a = Alumno.query.get_or_404(id)
    if request.method == 'POST':
        # Capturar estado anterior ANTES de modificar
        antes = {
            'nombre':     a.nombre_completo,
            'ci':         a.ci,
            'nacimiento': str(a.nacimiento) if a.nacimiento else None,
            'masculino':  a.masculino,
            'direccion':  a.direccion,
            'email':      a.email,
            'activo':     a.activo,
            'obs':        a.obs,
        }
        a.nombre     = request.form['nombre']
        a.paterno    = request.form.get('paterno')
        a.materno    = request.form.get('materno')
        a.nacimiento = date.fromisoformat(request.form['nacimiento']) if request.form.get('nacimiento') else None
        a.masculino  = request.form.get('genero') == 'M'
        a.ci         = request.form.get('ci') or None
        a.direccion  = request.form.get('direccion')
        a.email      = request.form.get('email')
        a.activo     = 'activo' in request.form
        a.obs        = request.form.get('obs')
        a.act = datetime.now()
        db.session.commit()
        # Registrar solo los campos que realmente cambiaron
        despues = {
            'nombre':     a.nombre_completo,
            'ci':         a.ci,
            'nacimiento': str(a.nacimiento) if a.nacimiento else None,
            'masculino':  a.masculino,
            'direccion':  a.direccion,
            'email':      a.email,
            'activo':     a.activo,
            'obs':        a.obs,
        }
        cambios = {k: {'antes': antes[k], 'despues': despues[k]}
                   for k in antes if antes[k] != despues[k]}
        log_accion('UPDATE', 'alumno', entidad_id=a.id,
                   detalle={'alumno': a.nombre_completo, 'cambios': cambios})
        flash('Alumno actualizado.', 'success')
        return redirect(url_for('alumno.index'))
    return render_template('alumno/form.html', alumno=a)

@alumno_bp.route('/<int:id>/eliminar', methods=['POST'])
@login_required
@permission_required('alumno_borrar')
def eliminar(id):
    a = Alumno.query.get_or_404(id)
    try:
        db.session.delete(a); db.session.commit(); flash('Alumno eliminado.', 'success')
    except Exception:
        db.session.rollback(); flash('No se puede eliminar: tiene registros relacionados.', 'danger')
    return redirect(url_for('alumno.index'))


# ── INSCRITO ──────────────────────────────────────────────
inscrito_bp = Blueprint('inscrito', __name__, url_prefix='/inscrito')

@inscrito_bp.route('/')
@login_required
@permission_required('inscrito_ver')
def index():
    q      = request.args.get('q', '').strip()
    estado = request.args.get('estado', '')       # inscrito | reserva | abandono | pendiente
    cur_id = request.args.get('cur_id', type=int)
    page   = request.args.get('page', 1, type=int)

    query = Inscrito.query.join(Alumno).join(Curso)

    if q:
        query = query.filter(
            db.or_(
                Alumno.nombre.ilike(f'%{q}%'),
                Alumno.paterno.ilike(f'%{q}%'),
                Alumno.materno.ilike(f'%{q}%'),
            )
        )
    if cur_id:
        query = query.filter(Inscrito.cur_id == cur_id)
    if estado == 'inscrito':
        query = query.filter(Inscrito.inscrito == True, Inscrito.abandono == False)
    elif estado == 'reserva':
        query = query.filter(Inscrito.reserva == True, Inscrito.abandono == False)
    elif estado == 'abandono':
        query = query.filter(Inscrito.abandono == True)
    elif estado == 'pendiente':
        query = query.filter(Inscrito.inscrito == False, Inscrito.reserva == False, Inscrito.abandono == False)

    query = query.order_by(Alumno.paterno, Alumno.nombre)
    pagination = query.paginate(page=page, per_page=PER_PAGE, error_out=False)

    cursos = Curso.query.order_by(Curso.gestion.desc(), Curso.paralelo).all()

    return render_template('inscrito/index.html',
        inscritos=pagination.items, pagination=pagination,
        q=q, estado=estado, cur_id=cur_id, cursos=cursos)

@inscrito_bp.route('/nuevo', methods=['GET', 'POST'])
@login_required
@permission_required('inscrito_crear')
def nuevo():
    alumnos = Alumno.query.filter_by(activo=True).order_by(Alumno.paterno).all()
    cursos  = Curso.query.order_by(Curso.gestion.desc(), Curso.paralelo).all()
    if request.method == 'POST':
        ins = Inscrito(
            alu_id=int(request.form['alu_id']), cur_id=int(request.form['cur_id']),
            reserva='reserva' in request.form, inscrito='inscrito' in request.form,
            descuento=int(request.form.get('descuento', 0)),
            motivo_descuento=request.form.get('motivo_descuento'),
            obs=request.form.get('obs'),
            creado=datetime.now(), act=datetime.now(), usu_id=current_user.id
        )
        db.session.add(ins); db.session.flush()
        costo = Costo.query.filter_by(cur_id=ins.cur_id).first()
        if ins.descuento != 100:
            if costo:
                for i in range(1, costo.nro_cuota + 1):
                    monto = float(costo.cuota) * (1 - ins.descuento / 100)
                    p = Pago(ins_id=ins.id, nro_cuota=i, cuota=round(monto, 2),
                             pagado=False, creado=datetime.now(), act=datetime.now(), usu_id=current_user.id)
                    db.session.add(p)
        db.session.commit()
        log_accion('CREATE', 'inscrito', entidad_id=ins.id, detalle={'alumno': ins.alumno.nombre_completo, 'cur_id': ins.cur_id, 'inscrito': ins.inscrito, 'reserva': ins.reserva})
        flash('Inscripción realizada. (Plan de pagos generado si descuento diferente a 100%.', 'success')
        return redirect(url_for('inscrito.index'))
    return render_template('inscrito/form.html', inscrito=None, alumnos=alumnos, cursos=cursos)

@inscrito_bp.route('/<int:id>/editar', methods=['GET', 'POST'])
@login_required
@permission_required('inscrito_editar')
def editar(id):
    ins = Inscrito.query.get_or_404(id)
    alumnos = Alumno.query.filter_by(activo=True).order_by(Alumno.paterno).all()
    cursos  = Curso.query.order_by(Curso.gestion.desc(), Curso.paralelo).all()
    if request.method == 'POST':
        ins.cur_id = int(request.form['cur_id'])
        ins.reserva = 'reserva' in request.form
        ins.inscrito = 'inscrito' in request.form
        ins.descuento = int(request.form.get('descuento', 0))
        ins.motivo_descuento = request.form.get('motivo_descuento')
        ins.abandono = 'abandono' in request.form
        ins.obs = request.form.get('obs'); ins.act = datetime.now()
        db.session.commit()
        log_accion('UPDATE', 'inscrito', entidad_id=ins.id, detalle={'alumno': ins.alumno.nombre_completo, 'inscrito': ins.inscrito, 'abandono': ins.abandono, 'descuento': ins.descuento})
        flash('Inscripción actualizada.', 'success')
        return redirect(url_for('inscrito.index'))
    return render_template('inscrito/form.html', inscrito=ins, alumnos=alumnos, cursos=cursos)


# ── NOTA ──────────────────────────────────────────────────
nota_bp = Blueprint('nota', __name__, url_prefix='/nota')

# ── Configuración de fechas de transcripción (parte del módulo nota) ──────────
import json as _json
import os as _os

_CONFIG_NOTAS_PATH = _os.path.normpath(
    _os.path.join(_os.path.dirname(__file__), '..', 'config_notas.json')
)

_CONFIG_NOTAS_DEFAULTS = {
    "habilitar_nota1": False, "transcripcion_nota1_inicio": "", "transcripcion_nota1_final": "",
    "habilitar_nota2": False, "transcripcion_nota2_inicio": "", "transcripcion_nota2_final": "",
    "habilitar_nota3": False, "transcripcion_nota3_inicio": "", "transcripcion_nota3_final": "",
}


def get_config_notas() -> dict:
    """Lee app/config_notas.json; si no existe retorna los valores por defecto."""
    if not _os.path.exists(_CONFIG_NOTAS_PATH):
        return dict(_CONFIG_NOTAS_DEFAULTS)
    try:
        with open(_CONFIG_NOTAS_PATH, 'r', encoding='utf-8') as f:
            data = _json.load(f)
        for k, v in _CONFIG_NOTAS_DEFAULTS.items():
            data.setdefault(k, v)
        return data
    except (_json.JSONDecodeError, OSError):
        return dict(_CONFIG_NOTAS_DEFAULTS)


def _save_config_notas(cfg: dict) -> None:
    with open(_CONFIG_NOTAS_PATH, 'w', encoding='utf-8') as f:
        _json.dump(cfg, f, ensure_ascii=False, indent=2)


def nota_periodo_habilitada(periodo: int, es_admin: bool = False) -> tuple:
    """Devuelve (permitido: bool, mensaje: str) para el período dado (1, 2 ó 3).
    Si es_admin=True siempre retorna (True, '') — el administrador no tiene restricciones."""
    if es_admin:
        return True, ''
    from datetime import date as _date
    cfg       = get_config_notas()
    habilitar = cfg.get(f'habilitar_nota{periodo}', False)
    inicio_s  = cfg.get(f'transcripcion_nota{periodo}_inicio', '')
    final_s   = cfg.get(f'transcripcion_nota{periodo}_final',  '')

    if not habilitar:
        return False, f'La transcripción del Período {periodo} está deshabilitada.'

    if inicio_s and final_s:
        try:
            hoy    = _date.today()
            inicio = _date.fromisoformat(inicio_s)
            final  = _date.fromisoformat(final_s)
            if not (inicio <= hoy <= final):
                return (
                    False,
                    f'La transcripción del Período {periodo} solo está permitida '
                    f'entre el {inicio.strftime("%d/%m/%Y")} y el {final.strftime("%d/%m/%Y")}.'
                )
        except ValueError:
            pass
    return True, ''


def get_estado_periodos(es_admin: bool = False) -> dict:
    """Retorna el estado de habilitación de cada período para usarlo en el template.
    Estructura: { 1: {'permitido': bool, 'msg': str}, 2: ..., 3: ... }"""
    resultado = {}
    for p in (1, 2, 3):
        permitido, msg = nota_periodo_habilitada(p, es_admin=es_admin)
        resultado[p] = {'permitido': permitido, 'msg': msg}
    return resultado


@nota_bp.route('/config-transcripcion', methods=['GET', 'POST'])
@login_required
def config_transcripcion():
    """Gestión de fechas de habilitación/restricción de transcripción de notas.
    Solo accesible para el rol 'administrador'."""
    if not current_user.has_role('administrador'):
        abort(403)

    cfg = get_config_notas()

    if request.method == 'POST':
        nueva_cfg = {}
        for p in ('1', '2', '3'):
            nueva_cfg[f'habilitar_nota{p}']            = f'habilitar_nota{p}' in request.form
            nueva_cfg[f'transcripcion_nota{p}_inicio'] = request.form.get(f'transcripcion_nota{p}_inicio', '').strip()
            nueva_cfg[f'transcripcion_nota{p}_final']  = request.form.get(f'transcripcion_nota{p}_final',  '').strip()

        errores = []
        for p in ('1', '2', '3'):
            ini = nueva_cfg[f'transcripcion_nota{p}_inicio']
            fin = nueva_cfg[f'transcripcion_nota{p}_final']
            if ini and fin:
                try:
                    from datetime import date as _date
                    if _date.fromisoformat(ini) > _date.fromisoformat(fin):
                        errores.append(f'Período {p}: la fecha de inicio no puede ser posterior a la fecha final.')
                except ValueError:
                    errores.append(f'Período {p}: formato de fecha inválido.')

        if errores:
            for e in errores:
                flash(e, 'danger')
            return render_template('nota/config_transcripcion.html', cfg=nueva_cfg)

        _save_config_notas(nueva_cfg)
        flash('Configuración de fechas de transcripción guardada correctamente.', 'success')
        return redirect(url_for('nota.config_transcripcion'))

    return render_template('nota/config_transcripcion.html', cfg=cfg)
# ── fin configuración transcripción ───────────────────────────────────────────


def _profesor_actual():
    """Retorna el Profesor vinculado al usuario en sesión, o None."""
    return Profesor.query.filter_by(usr_id_login=current_user.id).first()


def _asignaciones_profesor(profesor):
    """Retorna la lista de Asignado del profesor o [] si no existe."""
    if not profesor:
        return []
    return Asignado.query.filter_by(pro_id=profesor.id).all()


def _puede_editar_nota(nota):
    """Verifica si el usuario en sesión puede editar esta nota específica."""
    # admin y transcriptor: sin restricción
    if current_user.has_role('administrador') or current_user.has_role('transcriptor'):
        return True
    if current_user.has_role('profesor'):
        profesor = _profesor_actual()
        if not profesor:
            return False
        # Debe tener Asignado con ese cur_id + mat_id
        cur_id = nota.inscrito.cur_id
        return Asignado.query.filter_by(
            pro_id=profesor.id,
            cur_id=cur_id,
            mat_id=nota.mat_id
        ).first() is not None
    return False


@nota_bp.route('/')
@login_required
@permission_required('nota_ver')
def index():
    es_profesor = current_user.has_role('profesor')
    profesor    = _profesor_actual() if es_profesor else None

    cur_id = request.args.get('cur_id', type=int)
    mat_id = request.args.get('mat_id', type=int)
    q      = request.args.get('q', '').strip()
    page   = request.args.get('page', 1, type=int)

    # Cursos disponibles según rol
    if es_profesor and profesor:
        asig_ids = [a.cur_id for a in _asignaciones_profesor(profesor)]
        cursos   = Curso.query.filter(Curso.id.in_(asig_ids)).order_by(
                       Curso.gestion.desc(), Curso.paralelo).all()
        # Si el profesor no seleccionó curso, auto-seleccionar el primero
        if not cur_id and cursos:
            cur_id = cursos[0].id
    else:
        cursos = Curso.query.order_by(Curso.gestion.desc(), Curso.paralelo).all()

    # Materias disponibles para el filtro (filtradas por curso si aplica)
    if cur_id and es_profesor and profesor:
        mat_ids  = [a.mat_id for a in Asignado.query.filter_by(
                       pro_id=profesor.id, cur_id=cur_id).all()]
        materias = Materia.query.filter(Materia.id.in_(mat_ids)).order_by(Materia.materia).all()
    elif cur_id:
        mat_ids  = [a.mat_id for a in Asignado.query.filter_by(cur_id=cur_id).all()]
        materias = Materia.query.filter(Materia.id.in_(mat_ids)).order_by(Materia.materia).all()
    else:
        materias = []

    # Query base
    query = (Nota.query
             .join(Inscrito, Nota.ins_id == Inscrito.id)
             .join(Alumno,   Inscrito.alu_id == Alumno.id)
             .join(Materia,  Nota.mat_id == Materia.id))

    if cur_id:
        query = query.filter(Inscrito.cur_id == cur_id)

    # Restricción adicional para profesor: solo sus materias asignadas en ese curso
    if es_profesor and profesor and cur_id:
        query = query.filter(Nota.mat_id.in_([m.id for m in materias]))

    if mat_id:
        query = query.filter(Nota.mat_id == mat_id)

    if q:
        query = query.filter(
            db.or_(
                Alumno.nombre.ilike(f'%{q}%'),
                Alumno.paterno.ilike(f'%{q}%'),
                Alumno.materno.ilike(f'%{q}%'),
                Materia.materia.ilike(f'%{q}%'),
            )
        )

    query = query.order_by(Alumno.paterno, Alumno.nombre, Materia.materia)
    pagination = query.paginate(page=page, per_page=PER_PAGE, error_out=False)

    return render_template('nota/index.html',
                           notas=pagination.items,
                           pagination=pagination,
                           cursos=cursos,
                           materias=materias,
                           cur_id=cur_id,
                           mat_id=mat_id,
                           q=q,
                           total=pagination.total,
                           es_profesor=es_profesor,
                           profesor=profesor)


@nota_bp.route('/nueva', methods=['GET', 'POST'])
@login_required
@permission_required('nota_crear')
def nueva():
    es_profesor = current_user.has_role('profesor')
    profesor    = _profesor_actual() if es_profesor else None

    if es_profesor and not profesor:
        flash('Su usuario no tiene un profesor vinculado. Contacte al administrador.', 'danger')
        return redirect(url_for('nota.index'))

    if es_profesor:
        asignaciones = _asignaciones_profesor(profesor)
        cur_ids  = list({a.cur_id for a in asignaciones})
        mat_ids  = list({a.mat_id for a in asignaciones})
        inscritos = (Inscrito.query
                     .filter(Inscrito.inscrito == True, Inscrito.cur_id.in_(cur_ids))
                     .all())
        materias  = Materia.query.filter(Materia.id.in_(mat_ids)).order_by(Materia.materia).all()
        # pares válidos (cur_id, mat_id) para validar en POST
        pares_validos = {(a.cur_id, a.mat_id) for a in asignaciones}
    else:
        inscritos = Inscrito.query.filter_by(inscrito=True).all()
        materias  = Materia.query.order_by(Materia.materia).all()
        pares_validos = None

    if request.method == 'POST':
        ins_id = int(request.form['ins_id'])
        mat_id = int(request.form['mat_id'])

        # Validar restricción de profesor
        if es_profesor and pares_validos:
            ins = Inscrito.query.get(ins_id)
            if not ins or (ins.cur_id, mat_id) not in pares_validos:
                flash('No tiene permiso para registrar notas en esa combinación de curso/materia.', 'danger')
                return redirect(url_for('nota.index'))

        n1 = int(request.form.get('nota1', 0))
        n2 = int(request.form.get('nota2', 0))
        n3 = int(request.form.get('nota3', 0))

        # ── Validación de períodos (solo para profesor, admin queda exento) ──
        es_admin = current_user.has_role('administrador')
        bloqueos = []
        for periodo, valor in ((1, n1), (2, n2), (3, n3)):
            if valor != 0:
                permitido, msg = nota_periodo_habilitada(periodo, es_admin=es_admin)
                if not permitido:
                    bloqueos.append(msg)
        if bloqueos:
            for msg in bloqueos:
                flash(msg, 'warning')
            return redirect(url_for('nota.nueva'))
        # ─────────────────────────────────────────────────────────────────────

        nota_final = round((n1 + n2 + n3) / 3, 1)
        aprob = int(request.form.get('nota_aprob', 51))
        n = Nota(
            ins_id=ins_id, mat_id=mat_id,
            nota1=n1, nota2=n2, nota3=n3,
            nota_final=nota_final, nota_aprob=aprob,
            aprobado=nota_final >= aprob,
            obs=request.form.get('obs'),
            creado=datetime.now(), act=datetime.now(), usu_id=current_user.id
        )
        db.session.add(n); db.session.commit()
        log_accion('CREATE', 'nota', entidad_id=n.id, detalle={'ins_id': n.ins_id, 'mat_id': n.mat_id, 'nota_final': float(n.nota_final), 'aprobado': n.aprobado})
        flash('Nota registrada.', 'success')
        return redirect(url_for('nota.index'))

    es_admin = current_user.has_role('administrador')
    return render_template('nota/form.html', nota=None,
                           inscritos=inscritos, materias=materias,
                           es_profesor=es_profesor,
                           periodos=get_estado_periodos(es_admin=es_admin))


@nota_bp.route('/<int:id>/editar', methods=['GET', 'POST'])
@login_required
@permission_required('nota_editar')
def editar(id):
    n = Nota.query.get_or_404(id)

    if not _puede_editar_nota(n):
        flash('No tiene permiso para editar esta calificación.', 'danger')
        return redirect(url_for('nota.index'))

    es_profesor = current_user.has_role('profesor')
    profesor    = _profesor_actual() if es_profesor else None

    if es_profesor and profesor:
        asignaciones = _asignaciones_profesor(profesor)
        cur_ids  = list({a.cur_id for a in asignaciones})
        mat_ids  = list({a.mat_id for a in asignaciones})
        inscritos = (Inscrito.query
                     .filter(Inscrito.inscrito == True, Inscrito.cur_id.in_(cur_ids))
                     .all())
        materias  = Materia.query.filter(Materia.id.in_(mat_ids)).order_by(Materia.materia).all()
        pares_validos = {(a.cur_id, a.mat_id) for a in asignaciones}
    else:
        inscritos = Inscrito.query.filter_by(inscrito=True).all()
        materias  = Materia.query.order_by(Materia.materia).all()
        pares_validos = None

    if request.method == 'POST':
        if es_profesor and pares_validos:
            ins = Inscrito.query.get(n.ins_id)
            mat_id_post = int(request.form.get('mat_id', n.mat_id))
            if not ins or (ins.cur_id, mat_id_post) not in pares_validos:
                flash('No tiene permiso para editar notas en esa combinación de curso/materia.', 'danger')
                return redirect(url_for('nota.index'))

        nota1_anterior = n.nota1
        nota2_anterior = n.nota2
        nota3_anterior = n.nota3

        n.nota1 = int(request.form.get('nota1', 0))
        n.nota2 = int(request.form.get('nota2', 0))
        n.nota3 = int(request.form.get('nota3', 0))

        # ── Validación de períodos (solo para profesor, admin queda exento) ──
        es_admin = current_user.has_role('administrador')
        bloqueos = []
        cambios = {
            1: n.nota1 != nota1_anterior,
            2: n.nota2 != nota2_anterior,
            3: n.nota3 != nota3_anterior,
        }
        for periodo, cambio in cambios.items():
            if cambio:
                permitido, msg = nota_periodo_habilitada(periodo, es_admin=es_admin)
                if not permitido:
                    bloqueos.append(msg)
        if bloqueos:
            n.nota1 = nota1_anterior
            n.nota2 = nota2_anterior
            n.nota3 = nota3_anterior
            db.session.expunge(n)
            db.session.expire_all()
            for msg in bloqueos:
                flash(msg, 'warning')
            return redirect(url_for('nota.editar', id=n.id))
        # ─────────────────────────────────────────────────────────────────────

        n.nota_final = round((n.nota1 + n.nota2 + n.nota3) / 3, 1)
        n.nota_aprob = int(request.form.get('nota_aprob', 51))
        n.aprobado   = n.nota_final >= n.nota_aprob
        n.obs        = request.form.get('obs')
        n.act = datetime.now()
        db.session.commit()
        log_accion('UPDATE', 'nota', entidad_id=n.id, detalle={'ins_id': n.ins_id, 'mat_id': n.mat_id, 'nota1': n.nota1, 'nota2': n.nota2, 'nota3': n.nota3, 'nota_final': float(n.nota_final), 'aprobado': n.aprobado})
        flash('Nota actualizada.', 'success')
        return redirect(url_for('nota.index', cur_id=n.inscrito.cur_id))

    es_admin = current_user.has_role('administrador')
    return render_template('nota/form.html', nota=n,
                           inscritos=inscritos, materias=materias,
                           es_profesor=es_profesor,
                           periodos=get_estado_periodos(es_admin=es_admin))


# ── PAGO ──────────────────────────────────────────────────
pago_bp = Blueprint('pago', __name__, url_prefix='/pago')

@pago_bp.route('/')
@login_required
@permission_required('pago_ver')
def index():
    alu_id = request.args.get('alu_id', type=int)
    pagos = []
    alumno_sel = None
    if alu_id:
        alumno_sel = Alumno.query.get(alu_id)
        ins = Inscrito.query.filter_by(alu_id=alu_id).first()
        if ins:
            pagos = Pago.query.filter_by(ins_id=ins.id).order_by(Pago.nro_cuota).all()
    return render_template('pago/index.html', pagos=pagos,
                           alu_id=alu_id, alumno_sel=alumno_sel)

@pago_bp.route('/buscar-alumno')
@login_required
@permission_required('pago_ver')
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
        'ci': str(a.ci) if a.ci else '-',
        'activo': a.activo,
    } for a in resultados])

@pago_bp.route('/<int:id>/registrar', methods=['GET', 'POST'])
@login_required
@permission_required('pago_crear')
def registrar(id):
    pago = Pago.query.get_or_404(id)
    if request.method == 'POST':
        pago.pagado = True
        pago.metodo_pago = request.form.get('metodo_pago')
        pago.fecha_pago = datetime.fromisoformat(request.form['fecha_pago'])
        pago.referencia_pago = request.form.get('referencia_pago')
        pago.obs = request.form.get('obs')
        pago.act = datetime.now(); pago.usu_id = current_user.id
        db.session.commit()
        log_accion('UPDATE', 'pago', entidad_id=pago.id, detalle={'ins_id': pago.ins_id, 'nro_cuota': pago.nro_cuota, 'cuota': pago.cuota, 'metodo_pago': pago.metodo_pago, 'fecha_pago': str(pago.fecha_pago)})
        flash(f'Cuota {pago.nro_cuota} registrada como pagada.', 'success')
        ins = Inscrito.query.get(pago.ins_id)
        return redirect(url_for('pago.index', alu_id=ins.alu_id))
    otros_pagos = Pago.query.filter_by(ins_id=pago.ins_id).order_by(Pago.nro_cuota).all()
    return render_template('pago/form.html', pago=pago,
                           otros_pagos=otros_pagos,
                           today=datetime.now().strftime('%Y-%m-%dT%H:%M'))


@pago_bp.route('/actualiza-plan', methods=['GET', 'POST'])
@login_required
def actualiza_plan():
    """Actualiza el plan de pagos para todos los alumnos con reserva=True o
    inscrito=True aplicando las siguientes reglas:
      - Si el inscrito tiene AL MENOS UN pago con pagado=True → se omite por completo.
      - Si le faltan cuotas respecto al costo definido en su curso → se crean las faltantes.
      - Si ya tiene todas las cuotas y ninguna está pagada → se omite (nada que agregar).
    Solo disponible para el rol 'administrador'.
    """
    if not current_user.has_role('administrador'):
        abort(403)

    if request.method == 'POST':
        candidatos = Inscrito.query.filter(
            db.and_(
                db.or_(Inscrito.reserva == True, Inscrito.inscrito == True),
                Inscrito.descuento != 100
            )
        ).all()

        actualizados  = 0   # alumnos a los que se les añadieron cuotas faltantes
        sin_costo     = 0   # su curso no tiene costos definidos
        ya_completos  = 0   # ya tenían todas las cuotas, nada que agregar
        detalle       = []

        for ins in candidatos:
            # ── Obtener costos del curso ──
            costos = (Costo.query
                      .filter_by(cur_id=ins.cur_id)
                      .order_by(Costo.nro_cuota)
                      .all())
            if not costos:
                sin_costo += 1
                detalle.append({
                    'alumno': ins.alumno.nombre_completo,
                    'estado': 'sin_costo',
                    'msg': 'Sin costos definidos para su curso'
                })
                continue

            # ── Cuotas que ya existen para este inscrito (pagadas o no) ──
            # Los registros con pagado=True NO se tocan; pero su nro_cuota
            # cuenta como "ya presente" y no se vuelve a crear.
            pagos_actuales = Pago.query.filter_by(ins_id=ins.id).all()
            cuotas_existentes = {p.nro_cuota for p in pagos_actuales}
            cuotas_esperadas  = {c.nro_cuota for c in costos}
            cuotas_faltantes  = cuotas_esperadas - cuotas_existentes

            # Información de cuotas pagadas (solo para el mensaje de detalle)
            cuotas_pagadas_cnt = sum(1 for p in pagos_actuales if p.pagado)

            if not cuotas_faltantes:
                ya_completos += 1
                msg = f'Ya tiene las {len(costos)} cuota(s) — sin cambios'
                if cuotas_pagadas_cnt:
                    msg += f' ({cuotas_pagadas_cnt} pagada(s))'
                detalle.append({
                    'alumno': ins.alumno.nombre_completo,
                    'estado': 'completo',
                    'msg': msg
                })
                continue

            # ── Crear solo las cuotas faltantes (nunca tocar las existentes) ──
            costos_dict = {c.nro_cuota: c for c in costos}
            for nro in sorted(cuotas_faltantes):
                costo = costos_dict[nro]
                monto = float(costo.cuota)
                if ins.descuento and ins.descuento > 0:
                    monto = monto - (ins.descuento * monto) / 100
                    monto = round(monto, 2)
                p = Pago(
                    ins_id=ins.id,
                    nro_cuota=nro,
                    cuota=monto,
                    pagado=False,
                    metodo_pago='',
                    fecha_pago=None,
                    referencia_pago='',
                    obs='',
                    creado=datetime.now(),
                    act=datetime.now(),
                    usu_id=current_user.id
                )
                db.session.add(p)

            actualizados += 1
            msg = f'{len(cuotas_faltantes)} cuota(s) añadida(s)'
            if cuotas_pagadas_cnt:
                msg += f' ({cuotas_pagadas_cnt} cuota(s) pagada(s) conservada(s) sin cambios)'
            if ins.descuento:
                msg += f' — {ins.descuento}% de descuento aplicado'
            detalle.append({
                'alumno': ins.alumno.nombre_completo,
                'estado': 'actualizado',
                'msg': msg
            })

        db.session.commit()
        log_accion('BULK', 'pago', detalle={
            'accion': 'actualiza_plan',
            'actualizados': actualizados,
            'ya_completos': ya_completos,
            'sin_costo': sin_costo,
        })
        return render_template(
            'pago/actualiza_plan.html',
            ejecutado=True,
            actualizados=actualizados,
            ya_completos=ya_completos,
            sin_costo=sin_costo,
            detalle=detalle
        )

    # ── GET: pantalla de confirmación con vista previa ──
    total_candidatos = Inscrito.query.filter(
        db.or_(Inscrito.reserva == True, Inscrito.inscrito == True)
    ).count()

    return render_template(
        'pago/actualiza_plan.html',
        ejecutado=False,
        total_candidatos=total_candidatos
    )
