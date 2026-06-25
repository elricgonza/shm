from datetime import date, datetime
from flask_login import UserMixin
from app import db, login_manager


# ──────────────────────────────────────────────
# Auth / Usuarios
# ──────────────────────────────────────────────

@login_manager.user_loader
def load_user(user_id):
    return Usuario.query.get(int(user_id))


class Usuario(UserMixin, db.Model):
    __tablename__ = 'usuario'

    id       = db.Column(db.Integer, primary_key=True)
    usuario  = db.Column(db.String(80), unique=True, nullable=False)
    email    = db.Column(db.String(100), nullable=False)
    password = db.Column(db.String(255), nullable=False)
    activo   = db.Column(db.Boolean, default=True)
    last_login = db.Column(db.DateTime, nullable=False, default=datetime.now)
    creado   = db.Column(db.DateTime, default=datetime.utcnow)
    act      = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    roles = db.relationship('Rol', secondary='usuario_rol', back_populates='usuarios')

    def has_role(self, role_name):
        return any(r.rol == role_name for r in self.roles)

    def has_permission(self, perm_name):
        for role in self.roles:
            if any(p.permiso == perm_name for p in role.permisos):
                return True
        return False

    def __repr__(self):
        return f'<Usuario {self.usuario}>'


class Rol(db.Model):
    __tablename__ = 'rol'

    id          = db.Column(db.Integer, primary_key=True)
    rol         = db.Column(db.String(50), unique=True, nullable=False)
    descripcion = db.Column(db.String(255))
    creado      = db.Column(db.DateTime, default=datetime.utcnow)
    act         = db.Column(db.DateTime)

    usuarios  = db.relationship('Usuario', secondary='usuario_rol', back_populates='roles')
    permisos  = db.relationship('Permiso', secondary='rol_permiso', back_populates='roles')


class Permiso(db.Model):
    __tablename__ = 'permiso'

    id          = db.Column(db.Integer, primary_key=True)
    permiso     = db.Column(db.String(50), unique=True, nullable=False)
    descripcion = db.Column(db.String(255))
    creado      = db.Column(db.DateTime, default=datetime.utcnow)
    act         = db.Column(db.DateTime)

    roles = db.relationship('Rol', secondary='rol_permiso', back_populates='permisos')


usuario_rol = db.Table('usuario_rol',
    db.Column('usu_id', db.Integer, db.ForeignKey('usuario.id'), primary_key=True),
    db.Column('rol_id', db.Integer, db.ForeignKey('rol.id'), primary_key=True)
)

rol_permiso = db.Table('rol_permiso',
    db.Column('rol_id', db.Integer, db.ForeignKey('rol.id'), primary_key=True),
    db.Column('per_id', db.Integer, db.ForeignKey('permiso.id'), primary_key=True)
)


# ──────────────────────────────────────────────
# Módulo académico
# ──────────────────────────────────────────────

class Gestion(db.Model):
    __tablename__ = 'gestion'

    id      = db.Column(db.Integer, primary_key=True)
    gestion = db.Column(db.SmallInteger)
    plan    = db.Column(db.String(150), nullable=False)
    inicio  = db.Column(db.Date, nullable=False)
    fin     = db.Column(db.Date, nullable=False)
    activo  = db.Column(db.Boolean, nullable=False, default=True)
    creado  = db.Column(db.DateTime, nullable=False, default=datetime.now)
    act     = db.Column(db.DateTime, nullable=False, default=datetime.now, onupdate=datetime.now)
    usu_id  = db.Column(db.Integer, nullable=False)

    grados  = db.relationship('Grado', backref='gestion', lazy='dynamic')


class Grado(db.Model):
    __tablename__ = 'grado'

    id     = db.Column(db.Integer, primary_key=True)
    grado  = db.Column(db.String(255), nullable=False)
    nivel  = db.Column(db.String(150), nullable=False)
    ges_id = db.Column(db.Integer, db.ForeignKey('gestion.id', onupdate='CASCADE', ondelete='RESTRICT'), nullable=False)
    creado = db.Column(db.DateTime, nullable=False, default=datetime.now)
    act    = db.Column(db.DateTime, nullable=False, default=datetime.now, onupdate=datetime.now)
    usu_id = db.Column(db.Integer, nullable=False)

    materias = db.relationship('Materia', backref='grado', lazy='dynamic')
    cursos   = db.relationship('Curso', backref='grado', lazy='dynamic')


class Materia(db.Model):
    __tablename__ = 'materia'

    id      = db.Column(db.Integer, primary_key=True)
    materia = db.Column(db.String(150), nullable=False)
    gra_id  = db.Column(db.Integer, db.ForeignKey('grado.id', onupdate='CASCADE', ondelete='RESTRICT'), nullable=False)
    creado  = db.Column(db.DateTime, nullable=False, default=datetime.now)
    act     = db.Column(db.DateTime, nullable=False, default=datetime.now, onupdate=datetime.now)
    usu_id  = db.Column(db.Integer, nullable=False)


class Profesor(db.Model):
    __tablename__ = 'profesor'

    id          = db.Column(db.Integer, primary_key=True)
    nombre      = db.Column(db.String(100), nullable=False)
    paterno     = db.Column(db.String(50))
    materno     = db.Column(db.String(50))
    masculino   = db.Column(db.Boolean, nullable=False)
    ci          = db.Column(db.Integer)
    formacion   = db.Column(db.String(100))
    email       = db.Column(db.String(100))
    activo      = db.Column(db.Boolean, nullable=False, default=True)
    usr_id_login = db.Column(db.Integer)
    creado      = db.Column(db.DateTime, nullable=False, default=datetime.now)
    act         = db.Column(db.DateTime, nullable=False, default=datetime.now, onupdate=datetime.now)
    usu_id      = db.Column(db.Integer, nullable=False)

    @property
    def nombre_completo(self):
        return f"{self.nombre} {self.paterno or ''} {self.materno or ''}".strip()


class Curso(db.Model):
    __tablename__ = 'curso'

    id        = db.Column(db.Integer, primary_key=True)
    curso     = db.Column(db.String(150))
    paralelo  = db.Column(db.String(50), nullable=False)
    gra_id    = db.Column(db.Integer, db.ForeignKey('grado.id', onupdate='CASCADE', ondelete='RESTRICT'), nullable=False)
    aula      = db.Column(db.String(50))
    capacidad = db.Column(db.SmallInteger)
    gestion   = db.Column(db.SmallInteger, nullable=False)
    creado    = db.Column(db.DateTime, nullable=False, default=datetime.now)
    act       = db.Column(db.DateTime, nullable=False, default=datetime.now, onupdate=datetime.now)
    usu_id    = db.Column(db.Integer, nullable=False)

    inscritos  = db.relationship('Inscrito', backref='curso', lazy='dynamic')
    asignados  = db.relationship('Asignado', backref='curso', lazy='dynamic')
    costos     = db.relationship('Costo', backref='curso', lazy='dynamic')


class Asignado(db.Model):
    __tablename__ = 'asignado'

    id     = db.Column(db.Integer, primary_key=True)
    cur_id = db.Column(db.Integer, db.ForeignKey('curso.id', onupdate='CASCADE', ondelete='RESTRICT'), nullable=False)
    mat_id = db.Column(db.Integer, db.ForeignKey('materia.id', onupdate='CASCADE', ondelete='RESTRICT'), nullable=False)
    pro_id = db.Column(db.Integer, db.ForeignKey('profesor.id', onupdate='CASCADE', ondelete='RESTRICT'), nullable=True)
    creado = db.Column(db.DateTime, nullable=False, default=datetime.now)
    act    = db.Column(db.DateTime, nullable=False, default=datetime.now, onupdate=datetime.now)
    usu_id = db.Column(db.Integer, nullable=False)

    materia  = db.relationship('Materia', backref='asignaciones')
    profesor = db.relationship('Profesor', backref='asignaciones')


class Alumno(db.Model):
    __tablename__ = 'alumno'

    id           = db.Column(db.Integer, primary_key=True)
    nombre       = db.Column(db.String(100), nullable=False)
    paterno      = db.Column(db.String(100))
    materno      = db.Column(db.String(100))
    nacimiento   = db.Column(db.Date)
    masculino    = db.Column(db.Boolean, nullable=False)
    ci           = db.Column(db.Integer)
    direccion    = db.Column(db.String(150))
    email        = db.Column(db.String(100))
    activo       = db.Column(db.Boolean, nullable=False, default=True)
    obs          = db.Column(db.String(100))
    usr_id_login = db.Column(db.Integer)
    foto_ruta    = db.Column(db.String(150))
    creado       = db.Column(db.DateTime, nullable=False, default=datetime.now)
    act          = db.Column(db.DateTime, nullable=False, default=datetime.now, onupdate=datetime.now)
    usu_id       = db.Column(db.Integer, nullable=False)

    inscripcion = db.relationship('Inscrito', backref='alumno', uselist=False)

    @property
    def nombre_completo(self):
        return f"{self.nombre} {self.paterno or ''} {self.materno or ''}".strip()


class Inscrito(db.Model):
    __tablename__ = 'inscrito'

    id               = db.Column(db.Integer, primary_key=True)
    alu_id           = db.Column(db.Integer, db.ForeignKey('alumno.id', onupdate='CASCADE', ondelete='SET NULL'), unique=True)
    cur_id           = db.Column(db.Integer, db.ForeignKey('curso.id', onupdate='CASCADE', ondelete='SET NULL'))
    reserva          = db.Column(db.Boolean, default=False)
    inscrito         = db.Column(db.Boolean, nullable=False, default=False)
    descuento        = db.Column(db.SmallInteger, nullable=False, default=0)
    motivo_descuento = db.Column(db.String(100))
    abandono         = db.Column(db.Boolean, nullable=False, default=False)
    obs              = db.Column(db.String(200))
    creado           = db.Column(db.DateTime, nullable=False, default=datetime.now)
    act              = db.Column(db.DateTime, nullable=False, default=datetime.now, onupdate=datetime.now)
    usu_id           = db.Column(db.Integer, nullable=False)

    notas  = db.relationship('Nota', backref='inscrito', lazy='dynamic')
    pagos  = db.relationship('Pago', backref='inscrito', lazy='dynamic')


class Nota(db.Model):
    __tablename__ = 'nota'

    id          = db.Column(db.Integer, primary_key=True)
    ins_id      = db.Column(db.Integer, db.ForeignKey('inscrito.id', onupdate='CASCADE', ondelete='RESTRICT'), nullable=False)
    mat_id      = db.Column(db.Integer, db.ForeignKey('materia.id'), nullable=False)
    nota1       = db.Column(db.SmallInteger, nullable=False, default=0)
    nota2       = db.Column(db.SmallInteger, nullable=False, default=0)
    nota3       = db.Column(db.SmallInteger, nullable=False, default=0)
    nota_final  = db.Column(db.Numeric(5, 1), nullable=False, default=0)
    nota_aprob  = db.Column(db.SmallInteger, nullable=False, default=51)
    aprobado    = db.Column(db.Boolean)
    obs         = db.Column(db.String(150))
    creado      = db.Column(db.DateTime, nullable=False, default=datetime.now)
    act         = db.Column(db.DateTime, nullable=False, default=datetime.now, onupdate=datetime.now)
    usu_id      = db.Column(db.Integer, nullable=False)

    materia = db.relationship('Materia', backref='notas')


class Costo(db.Model):
    __tablename__ = 'costo'

    id        = db.Column(db.Integer, primary_key=True)
    cur_id    = db.Column(db.Integer, db.ForeignKey('curso.id', onupdate='CASCADE', ondelete='RESTRICT'), nullable=False)
    nro_cuota = db.Column(db.SmallInteger, nullable=False)
    cuota     = db.Column(db.Numeric(10, 2), nullable=False)
    obs       = db.Column(db.String(200), nullable=False)
    creado    = db.Column(db.DateTime, nullable=False, default=datetime.now)
    act       = db.Column(db.DateTime, nullable=False, default=datetime.now, onupdate=datetime.now)
    usu_id    = db.Column(db.Integer, nullable=False)


class Pago(db.Model):
    __tablename__ = 'pago'

    id              = db.Column(db.Integer, primary_key=True)
    ins_id          = db.Column(db.Integer, db.ForeignKey('inscrito.id', onupdate='CASCADE', ondelete='RESTRICT'), nullable=False)
    nro_cuota       = db.Column(db.SmallInteger, nullable=False)
    cuota           = db.Column(db.Float, nullable=False)
    pagado          = db.Column(db.Boolean, default=False)
    metodo_pago     = db.Column(db.String(50))
    fecha_pago      = db.Column(db.DateTime)
    referencia_pago = db.Column(db.String(100))
    obs             = db.Column(db.String(100))
    creado          = db.Column(db.DateTime, nullable=False, default=datetime.now)
    act             = db.Column(db.DateTime, nullable=False, default=datetime.now, onupdate=datetime.now)
    usu_id          = db.Column(db.Integer, nullable=False)


class AuditLog(db.Model):
    __tablename__ = 'audit_log'

    id         = db.Column(db.Integer, primary_key=True)
    usu_id     = db.Column(db.Integer, db.ForeignKey('usuario.id', ondelete='SET NULL'), nullable=True)
    usuario    = db.Column(db.String(80), nullable=False, default='anónimo')
    accion     = db.Column(db.String(20), nullable=False)   # CREATE UPDATE DELETE LOGIN LOGOUT BULK ERROR
    modulo     = db.Column(db.String(50), nullable=False)   # grado, materia, alumno, pago, ...
    entidad_id = db.Column(db.Integer, nullable=True)
    detalle    = db.Column(db.Text, nullable=True)          # JSON con datos relevantes
    ip         = db.Column(db.String(45), nullable=True)
    endpoint   = db.Column(db.String(150), nullable=True)
    metodo     = db.Column(db.String(10), nullable=True)
    status     = db.Column(db.SmallInteger, nullable=True, default=200)
    creado     = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    autor = db.relationship('Usuario', backref='audit_logs', foreign_keys=[usu_id])
