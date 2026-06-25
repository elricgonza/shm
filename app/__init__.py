from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_bcrypt import Bcrypt
from config import Config

db = SQLAlchemy()
login_manager = LoginManager()
bcrypt = Bcrypt()


def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    db.init_app(app)
    bcrypt.init_app(app)
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'
    login_manager.login_message = 'Por favor inicie sesión para acceder.'
    login_manager.login_message_category = 'warning'

    from app.routes.auth import auth_bp
    from app.routes.admin import admin_bp
    from app.routes.gestion import gestion_bp
    from app.routes.grado import grado_bp
    from app.routes.materia import materia_bp
    from app.routes.profesor import profesor_bp
    from app.routes.curso import curso_bp
    from app.routes.alumno import alumno_bp
    from app.routes.inscrito import inscrito_bp
    from app.routes.nota import nota_bp
    from app.routes.pago import pago_bp
    from app.routes.dashboard import dashboard_bp
    from app.routes.asignado import asignado_bp
    from app.routes.costo import costo_bp
    from app.routes.anulacion import anulacion_bp
    from app.routes.historial import historial_bp
    from app.routes.reportes import reportes_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(gestion_bp)
    app.register_blueprint(grado_bp)
    app.register_blueprint(materia_bp)
    app.register_blueprint(profesor_bp)
    app.register_blueprint(curso_bp)
    app.register_blueprint(alumno_bp)
    app.register_blueprint(inscrito_bp)
    app.register_blueprint(nota_bp)
    app.register_blueprint(pago_bp)
    app.register_blueprint(dashboard_bp)
    app.register_blueprint(asignado_bp)
    app.register_blueprint(costo_bp)
    app.register_blueprint(anulacion_bp)
    app.register_blueprint(historial_bp)
    app.register_blueprint(reportes_bp)

    return app
