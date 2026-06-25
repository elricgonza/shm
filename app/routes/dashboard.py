from flask import Blueprint, render_template
from flask_login import login_required
from app.models import Alumno, Curso, Profesor, Inscrito, Pago, Gestion

dashboard_bp = Blueprint('dashboard', __name__)


@dashboard_bp.route('/')
@login_required
def index():
    stats = {
        'alumnos':    Alumno.query.filter_by(activo=True).count(),
        'cursos':     Curso.query.count(),
        'profesores': Profesor.query.filter_by(activo=True).count(),
        'inscritos':  Inscrito.query.filter_by(inscrito=True).count(),
        'pagos_pendientes': Pago.query.filter_by(pagado=False).count(),
    }
    gestion_activa = Gestion.query.filter_by(activo=True).first()
    return render_template('dashboard.html', stats=stats, gestion=gestion_activa)
