from werkzeug.security import check_password_hash, generate_password_hash
from datetime import datetime

from flask_sqlalchemy import SQLAlchemy


db = SQLAlchemy()


class Usuario(db.Model):
    __tablename__ = 'Usuarios'

    Id = db.Column(db.Integer, primary_key=True)
    Nombre = db.Column(db.String(100), nullable=False)
    Apellido = db.Column(db.String(50), nullable=False)
    DNI = db.Column(db.String(20), unique=True, nullable=False)
    Rol = db.Column(db.String(50), nullable=False)


class Credencial(db.Model):
    __tablename__ = 'Credenciales'

    Id = db.Column(db.Integer, primary_key=True)
    DNI = db.Column(db.String(20), unique=True, nullable=False)
    PasswordHash = db.Column(db.String(255), nullable=False)
    Activo = db.Column(db.Boolean, nullable=False, default=True)

    def set_password(self, plain_password: str) -> None:
        self.PasswordHash = generate_password_hash(plain_password)

    def check_password(self, plain_password: str) -> bool:
        return check_password_hash(self.PasswordHash, plain_password)


class BitacoraGestion(db.Model):
    __tablename__ = 'BitacoraGestiones'

    Id = db.Column(db.Integer, primary_key=True)
    UsuarioDNI = db.Column(db.String(20), nullable=False)
    UsuarioNombre = db.Column(db.String(160), nullable=True)
    Accion = db.Column(db.String(255), nullable=False)
    Parametros = db.Column(db.Text, nullable=True)
    Resultado = db.Column(db.String(255), nullable=True)
    Equipo = db.Column(db.String(255), nullable=True)
    Fecha = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)


class ProcesoArchivo(db.Model):
    __tablename__ = 'ProcesosArchivos'

    Id = db.Column(db.Integer, primary_key=True)
    Gestion = db.Column(db.String(120), nullable=False, index=True)
    Descripcion = db.Column(db.String(255), nullable=True)
    NombreOriginal = db.Column(db.String(255), nullable=False)
    NombreGuardado = db.Column(db.String(255), nullable=False, unique=True)
    TipoMime = db.Column(db.String(120), nullable=True)
    TamanioBytes = db.Column(db.Integer, nullable=False)
    SubidoPorDNI = db.Column(db.String(20), nullable=False)
    SubidoPorNombre = db.Column(db.String(160), nullable=True)
    FechaSubida = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
