from functools import wraps
import os
import re
import subprocess
import ctypes
import json
import uuid
from datetime import datetime, timedelta

from flask import Blueprint, current_app, jsonify, request, send_from_directory, session
from sqlalchemy import text
from werkzeug.utils import secure_filename

from .models import BitacoraGestion, Credencial, ProcesoArchivo, Usuario, db

bp = Blueprint('main', __name__)

ALLOWED_PROCESOS_EXTENSIONS = {
    'pdf', 'doc', 'docx', 'xls', 'xlsx', 'ppt', 'pptx',
    'txt', 'csv', 'png', 'jpg', 'jpeg', 'webp', 'zip'
}


def login_required(view_func):
    @wraps(view_func)
    def wrapped(*args, **kwargs):
        if not session.get('dni'):
            return jsonify({'error': 'No autenticado'}), 401
        return view_func(*args, **kwargs)

    return wrapped


def role_required(*roles):
    def decorator(view_func):
        @wraps(view_func)
        def wrapped(*args, **kwargs):
            user_role = session.get('rol')
            if user_role not in roles:
                return jsonify({'error': 'No autorizado'}), 403
            return view_func(*args, **kwargs)

        return wrapped

    return decorator


def valid_network_target(value):
    # Hostnames/IPs only, avoid command injection and malformed values.
    if not value:
        return False
    if len(value) > 255:
        return False
    if value.startswith('-'):
        return False
    return re.fullmatch(r'[A-Za-z0-9.-]+', value) is not None


def allowed_procesos_file(filename):
    if not filename or '.' not in filename:
        return False
    ext = filename.rsplit('.', 1)[1].lower()
    return ext in ALLOWED_PROCESOS_EXTENSIONS


def is_superadmin_dni(dni):
    configured_superadmin = os.getenv('SUPERADMIN_DNI', '').strip()
    return bool(configured_superadmin) and str(dni or '').strip() == configured_superadmin


def superadmin_required(view_func):
    @wraps(view_func)
    def wrapped(*args, **kwargs):
        if not is_superadmin_dni(session.get('dni')):
            return jsonify({'error': 'Requiere permisos de superadmin'}), 403
        return view_func(*args, **kwargs)

    return wrapped


def registrar_bitacora(accion, parametros=None, resultado=None, equipo=None):
    usuario_dni = session.get('dni') or 'desconocido'
    usuario_nombre = session.get('nombre') or ''
    equipo_final = equipo or request.headers.get('X-Client-Host') or request.remote_addr or ''

    if parametros is None:
        parametros_str = None
    elif isinstance(parametros, str):
        parametros_str = parametros
    else:
        parametros_str = json.dumps(parametros, ensure_ascii=True)

    entry = BitacoraGestion(
        UsuarioDNI=usuario_dni,
        UsuarioNombre=usuario_nombre,
        Accion=accion,
        Parametros=parametros_str,
        Resultado=resultado,
        Equipo=str(equipo_final)[:255] if equipo_final else None,
    )
    db.session.add(entry)


@bp.route('/', methods=['GET'])
def index():
    return jsonify({
        'status': 'online',
        'message': 'API Flask funcionando correctamente',
        'endpoints': {
            '/auth/login': 'POST - Iniciar sesion',
            '/auth/logout': 'POST - Cerrar sesion',
            '/auth/me': 'GET - Usuario autenticado actual',
            '/auth/change-password': 'POST - Cambiar password del usuario autenticado',
            '/auth/signup': 'POST - Crear cuenta (publico)',
            '/auth/register': 'POST - Crear credencial (admin)',
            '/admin/users': 'GET - Listar usuarios (solo superadmin)',
            '/admin/users/<id>': 'PATCH - Actualizar rol/estado (solo superadmin)',
            '/admin/bitacora': 'GET - Bitacora con filtros (solo superadmin)',
            '/procesos/files': 'GET/POST - Listar o subir archivos de procesos (requiere sesion)',
            '/procesos/files/<id>/download': 'GET - Descargar archivo de procesos (requiere sesion)',
            '/usuario/<dni>': 'GET - Obtener usuario por DNI (requiere sesion)',
            '/log_gestion': 'POST - Registrar gestion (requiere sesion)'
        }
    })


@bp.route('/auth/login', methods=['POST'])
def login():
    data = request.get_json(silent=True) or {}
    dni = str(data.get('dni', '')).strip()
    password = str(data.get('password', ''))

    if not dni or not password:
        return jsonify({'error': 'DNI y password son obligatorios'}), 400

    credencial = Credencial.query.filter_by(DNI=dni, Activo=True).first()
    if not credencial or not credencial.check_password(password):
        return jsonify({'error': 'Credenciales invalidas'}), 401

    usuario = Usuario.query.filter_by(DNI=dni).first()
    if not usuario:
        return jsonify({'error': 'Usuario no encontrado'}), 404

    session.permanent = True
    session['dni'] = usuario.DNI
    session['rol'] = usuario.Rol
    session['nombre'] = f'{usuario.Nombre} {usuario.Apellido}'.strip()

    return jsonify({
        'message': 'Login correcto',
        'usuario': {
            'Id': usuario.Id,
            'Nombre': usuario.Nombre,
            'Apellido': usuario.Apellido,
            'DNI': usuario.DNI,
            'Rol': usuario.Rol,
            'EsSuperadmin': is_superadmin_dni(usuario.DNI)
        }
    })


@bp.route('/auth/logout', methods=['POST'])
@login_required
def logout():
    session.clear()
    return jsonify({'message': 'Sesion cerrada'})


@bp.route('/auth/me', methods=['GET'])
@login_required
def me():
    return jsonify({
        'dni': session.get('dni'),
        'rol': session.get('rol'),
        'nombre': session.get('nombre'),
        'es_superadmin': is_superadmin_dni(session.get('dni'))
    })


@bp.route('/auth/change-password', methods=['POST'])
@login_required
def change_password():
    data = request.get_json(silent=True) or {}
    current_password = str(data.get('current_password', ''))
    new_password = str(data.get('new_password', ''))

    if not current_password or not new_password:
        return jsonify({'error': 'current_password y new_password son obligatorios'}), 400

    if len(new_password) < 8:
        return jsonify({'error': 'La nueva password debe tener al menos 8 caracteres'}), 400

    if current_password == new_password:
        return jsonify({'error': 'La nueva password debe ser diferente de la actual'}), 400

    dni = session.get('dni')
    credencial = Credencial.query.filter_by(DNI=dni, Activo=True).first()
    if not credencial:
        return jsonify({'error': 'No se encontro credencial activa para el usuario'}), 404

    if not credencial.check_password(current_password):
        return jsonify({'error': 'La password actual es incorrecta'}), 401

    credencial.set_password(new_password)
    db.session.commit()

    return jsonify({'message': 'Password actualizada correctamente'})


@bp.route('/auth/register', methods=['POST'])
def register_auth_user():
    data = request.get_json(silent=True) or {}
    dni = str(data.get('dni', '')).strip()
    password = str(data.get('password', ''))
    activo = bool(data.get('activo', True))

    if not dni or not password:
        return jsonify({'error': 'DNI y password son obligatorios'}), 400

    bootstrap_token = request.headers.get('X-Bootstrap-Token', '')
    expected_bootstrap_token = os.getenv('ADMIN_BOOTSTRAP_TOKEN', '')
    has_admin_session = session.get('rol') == 'Administrador'

    if not has_admin_session:
        if not expected_bootstrap_token or bootstrap_token != expected_bootstrap_token:
            return jsonify({'error': 'Solo un administrador puede crear credenciales'}), 403

    usuario = Usuario.query.filter_by(DNI=dni).first()
    if not usuario:
        return jsonify({'error': 'No existe un usuario con ese DNI en Usuarios'}), 404

    credencial = Credencial.query.filter_by(DNI=dni).first()
    if credencial is None:
        credencial = Credencial(DNI=dni, Activo=activo)
        credencial.set_password(password)
        db.session.add(credencial)
    else:
        credencial.Activo = activo
        credencial.set_password(password)

    db.session.commit()
    return jsonify({'message': 'Credencial creada/actualizada correctamente', 'dni': dni})


@bp.route('/auth/signup', methods=['POST'])
def signup():
    data = request.get_json(silent=True) or {}
    nombre = str(data.get('nombre', '')).strip()
    apellido = str(data.get('apellido', '')).strip()
    dni = str(data.get('dni', '')).strip()
    password = str(data.get('password', ''))

    if not nombre or not apellido or not dni or not password:
        return jsonify({'error': 'Nombre, apellido, DNI y password son obligatorios'}), 400

    if len(password) < 8:
        return jsonify({'error': 'La password debe tener al menos 8 caracteres'}), 400

    usuario_existente = Usuario.query.filter_by(DNI=dni).first()
    if usuario_existente and Credencial.query.filter_by(DNI=dni).first():
        return jsonify({'error': 'Ya existe una cuenta con ese DNI'}), 409

    if usuario_existente is None:
        usuario_existente = Usuario(
            Nombre=nombre,
            Apellido=apellido,
            DNI=dni,
            Rol='Asesor'
        )
        db.session.add(usuario_existente)
    else:
        usuario_existente.Nombre = nombre
        usuario_existente.Apellido = apellido
        if not usuario_existente.Rol:
            usuario_existente.Rol = 'Asesor'

    credencial = Credencial.query.filter_by(DNI=dni).first()
    if credencial is None:
        credencial = Credencial(DNI=dni, Activo=True)
        db.session.add(credencial)

    credencial.Activo = True
    credencial.set_password(password)

    db.session.commit()

    return jsonify({
        'message': 'Cuenta creada correctamente',
        'dni': usuario_existente.DNI,
        'rol': usuario_existente.Rol
    }), 201


@bp.route('/usuario/<dni>', methods=['GET'])
@login_required
def get_usuario_por_dni(dni):
    usuario = Usuario.query.filter_by(DNI=dni).first()
    if usuario:
        return jsonify({
            'Id': usuario.Id,
            'Nombre': usuario.Nombre,
            'Apellido': usuario.Apellido,
            'DNI': usuario.DNI,
            'Rol': usuario.Rol
        })
    return jsonify({'error': 'Usuario no encontrado'}), 404


@bp.route('/log_gestion', methods=['POST'])
@login_required
def log_gestion():
    data = request.get_json(silent=True) or {}
    dni = str(data.get('dni', '')).strip() or str(session.get('dni', '')).strip()
    accion = str(data.get('accion', '')).strip()
    parametros = data.get('parametros')
    resultado = str(data.get('resultado', '')).strip() or 'ok'
    equipo = str(data.get('equipo', '')).strip()

    if not dni or not accion:
        return jsonify({'error': 'dni y accion son obligatorios'}), 400

    db.session.execute(
        text('INSERT INTO Gestiones (DNI, Accion) VALUES (:dni, :accion)'),
        {'dni': dni, 'accion': accion}
    )

    registrar_bitacora(
        accion=accion,
        parametros=parametros,
        resultado=resultado,
        equipo=equipo,
    )

    db.session.commit()

    return jsonify({'status': 'ok'})


@bp.route('/tools/ping', methods=['POST'])
@login_required
@role_required('Administrador', 'Estructura')
def tool_ping():
    data = request.get_json(silent=True) or {}
    target = str(data.get('target', '')).strip()
    count = int(data.get('count', 4)) if str(data.get('count', '')).strip() else 4

    if not valid_network_target(target):
        return jsonify({'error': 'Target invalido para ping'}), 400

    if count < 1 or count > 10:
        return jsonify({'error': 'count debe estar entre 1 y 10'}), 400

    completed = subprocess.run(
        ['ping', '-n', str(count), target],
        capture_output=True,
        text=True,
        timeout=30,
        check=False,
    )

    output = (completed.stdout or '') + (completed.stderr or '')
    registrar_bitacora(
        accion='Ping',
        parametros={'target': target, 'count': count},
        resultado='ok' if completed.returncode == 0 else f'error_{completed.returncode}',
    )
    db.session.commit()

    return jsonify({
        'target': target,
        'exit_code': completed.returncode,
        'output': output,
    })


@bp.route('/tools/tracert', methods=['POST'])
@login_required
@role_required('Administrador', 'Estructura')
def tool_tracert():
    data = request.get_json(silent=True) or {}
    target = str(data.get('target', '')).strip()
    max_hops = int(data.get('max_hops', 15)) if str(data.get('max_hops', '')).strip() else 15

    if not valid_network_target(target):
        return jsonify({'error': 'Target invalido para tracert'}), 400

    if max_hops < 1 or max_hops > 30:
        return jsonify({'error': 'max_hops debe estar entre 1 y 30'}), 400

    completed = subprocess.run(
        ['tracert', '-d', '-h', str(max_hops), target],
        capture_output=True,
        text=True,
        timeout=90,
        check=False,
    )

    output = (completed.stdout or '') + (completed.stderr or '')
    registrar_bitacora(
        accion='Tracert',
        parametros={'target': target, 'max_hops': max_hops},
        resultado='ok' if completed.returncode == 0 else f'error_{completed.returncode}',
    )
    db.session.commit()

    return jsonify({
        'target': target,
        'exit_code': completed.returncode,
        'output': output,
    })


@bp.route('/tools/resolution', methods=['POST'])
@login_required
@role_required('Administrador', 'Estructura')
def tool_resolution():
    data = request.get_json(silent=True) or {}

    try:
        width = int(data.get('width', 0))
        height = int(data.get('height', 0))
    except (TypeError, ValueError):
        return jsonify({'error': 'width y height deben ser numericos'}), 400

    if width < 800 or width > 7680 or height < 600 or height > 4320:
        return jsonify({'error': 'Resolucion fuera de rango permitido'}), 400

    class DEVMODE(ctypes.Structure):
        _fields_ = [
            ('dmDeviceName', ctypes.c_wchar * 32),
            ('dmSpecVersion', ctypes.c_ushort),
            ('dmDriverVersion', ctypes.c_ushort),
            ('dmSize', ctypes.c_ushort),
            ('dmDriverExtra', ctypes.c_ushort),
            ('dmFields', ctypes.c_ulong),
            ('dmPositionX', ctypes.c_long),
            ('dmPositionY', ctypes.c_long),
            ('dmDisplayOrientation', ctypes.c_ulong),
            ('dmDisplayFixedOutput', ctypes.c_ulong),
            ('dmColor', ctypes.c_short),
            ('dmDuplex', ctypes.c_short),
            ('dmYResolution', ctypes.c_short),
            ('dmTTOption', ctypes.c_short),
            ('dmCollate', ctypes.c_short),
            ('dmFormName', ctypes.c_wchar * 32),
            ('dmLogPixels', ctypes.c_ushort),
            ('dmBitsPerPel', ctypes.c_ulong),
            ('dmPelsWidth', ctypes.c_ulong),
            ('dmPelsHeight', ctypes.c_ulong),
            ('dmDisplayFlags', ctypes.c_ulong),
            ('dmDisplayFrequency', ctypes.c_ulong),
            ('dmICMMethod', ctypes.c_ulong),
            ('dmICMIntent', ctypes.c_ulong),
            ('dmMediaType', ctypes.c_ulong),
            ('dmDitherType', ctypes.c_ulong),
            ('dmReserved1', ctypes.c_ulong),
            ('dmReserved2', ctypes.c_ulong),
            ('dmPanningWidth', ctypes.c_ulong),
            ('dmPanningHeight', ctypes.c_ulong),
        ]

    devmode = DEVMODE()
    devmode.dmSize = ctypes.sizeof(DEVMODE)

    if ctypes.windll.user32.EnumDisplaySettingsW(None, -1, ctypes.byref(devmode)) == 0:
        return jsonify({'error': 'No se pudo obtener DEVMODE del display'}), 500

    DM_PELSWIDTH = 0x80000
    DM_PELSHEIGHT = 0x100000
    devmode.dmPelsWidth = width
    devmode.dmPelsHeight = height
    devmode.dmFields = DM_PELSWIDTH | DM_PELSHEIGHT

    result = ctypes.windll.user32.ChangeDisplaySettingsW(ctypes.byref(devmode), 0)
    if result != 0:
        return jsonify({'error': f'No se pudo cambiar resolucion. Codigo {result}'}), 500

    registrar_bitacora(
        accion='Cambio Resolucion',
        parametros={'width': width, 'height': height},
        resultado='ok',
    )
    db.session.commit()

    return jsonify({'message': f'Resolucion actualizada a {width}x{height}'})


@bp.route('/admin/users', methods=['GET'])
@login_required
@superadmin_required
def admin_list_users():
    usuarios = Usuario.query.order_by(Usuario.Id.asc()).all()

    payload = []
    for usuario in usuarios:
        credencial = Credencial.query.filter_by(DNI=usuario.DNI).first()
        payload.append({
            'Id': usuario.Id,
            'Nombre': usuario.Nombre,
            'Apellido': usuario.Apellido,
            'DNI': usuario.DNI,
            'Rol': usuario.Rol,
            'Activo': credencial.Activo if credencial else False,
        })

    return jsonify({'users': payload})


@bp.route('/admin/users/<int:user_id>', methods=['PATCH'])
@login_required
@superadmin_required
def admin_update_user(user_id):
    data = request.get_json(silent=True) or {}
    nuevo_rol = data.get('rol')
    activo = data.get('activo')

    usuario = Usuario.query.get(user_id)
    if not usuario:
        return jsonify({'error': 'Usuario no encontrado'}), 404

    if usuario.DNI == session.get('dni') and nuevo_rol and nuevo_rol != 'Administrador':
        return jsonify({'error': 'No puedes quitarte tu propio rol Administrador'}), 400

    if nuevo_rol is not None:
        rol_normalizado = str(nuevo_rol).strip()
        roles_validos = {'Administrador', 'Asesor', 'Estructura', 'Procesos'}
        if rol_normalizado not in roles_validos:
            return jsonify({'error': 'Rol invalido'}), 400
        usuario.Rol = rol_normalizado

    if activo is not None:
        credencial = Credencial.query.filter_by(DNI=usuario.DNI).first()
        if credencial is None:
            return jsonify({'error': 'El usuario no tiene credencial creada'}), 404
        credencial.Activo = bool(activo)

    registrar_bitacora(
        accion='Admin actualizar usuario',
        parametros={'user_id': user_id, 'rol': nuevo_rol, 'activo': activo},
        resultado='ok',
    )

    db.session.commit()

    credencial_actualizada = Credencial.query.filter_by(DNI=usuario.DNI).first()
    return jsonify({
        'message': 'Usuario actualizado correctamente',
        'user': {
            'Id': usuario.Id,
            'Nombre': usuario.Nombre,
            'Apellido': usuario.Apellido,
            'DNI': usuario.DNI,
            'Rol': usuario.Rol,
            'Activo': credencial_actualizada.Activo if credencial_actualizada else False,
        }
    })


@bp.route('/admin/bitacora', methods=['GET'])
@login_required
@superadmin_required
def admin_bitacora():
    fecha_desde_str = (request.args.get('fecha_desde') or '').strip()
    fecha_hasta_str = (request.args.get('fecha_hasta') or '').strip()
    usuario = (request.args.get('usuario') or '').strip()
    accion = (request.args.get('accion') or '').strip()

    query = BitacoraGestion.query

    if fecha_desde_str:
        try:
            fecha_desde = datetime.strptime(fecha_desde_str, '%Y-%m-%d')
            query = query.filter(BitacoraGestion.Fecha >= fecha_desde)
        except ValueError:
            return jsonify({'error': 'fecha_desde invalida. Usa formato YYYY-MM-DD'}), 400

    if fecha_hasta_str:
        try:
            fecha_hasta = datetime.strptime(fecha_hasta_str, '%Y-%m-%d') + timedelta(days=1)
            query = query.filter(BitacoraGestion.Fecha < fecha_hasta)
        except ValueError:
            return jsonify({'error': 'fecha_hasta invalida. Usa formato YYYY-MM-DD'}), 400

    if usuario:
        query = query.filter(
            (BitacoraGestion.UsuarioDNI.ilike(f'%{usuario}%')) |
            (BitacoraGestion.UsuarioNombre.ilike(f'%{usuario}%'))
        )

    if accion:
        query = query.filter(BitacoraGestion.Accion.ilike(f'%{accion}%'))

    rows = query.order_by(BitacoraGestion.Fecha.desc()).limit(500).all()

    return jsonify({
        'items': [
            {
                'Id': r.Id,
                'UsuarioDNI': r.UsuarioDNI,
                'UsuarioNombre': r.UsuarioNombre,
                'Accion': r.Accion,
                'Parametros': r.Parametros,
                'Resultado': r.Resultado,
                'Timestamp': r.Fecha.isoformat(),
                'Equipo': r.Equipo,
            }
            for r in rows
        ]
    })


@bp.route('/procesos/files', methods=['GET'])
@login_required
def procesos_list_files():
    gestion = (request.args.get('gestion') or '').strip()

    query = ProcesoArchivo.query
    if gestion:
        query = query.filter(ProcesoArchivo.Gestion.ilike(f'%{gestion}%'))

    rows = query.order_by(ProcesoArchivo.FechaSubida.desc()).limit(300).all()
    return jsonify({
        'items': [
            {
                'Id': r.Id,
                'Gestion': r.Gestion,
                'Descripcion': r.Descripcion,
                'NombreOriginal': r.NombreOriginal,
                'TipoMime': r.TipoMime,
                'TamanioBytes': r.TamanioBytes,
                'SubidoPorDNI': r.SubidoPorDNI,
                'SubidoPorNombre': r.SubidoPorNombre,
                'FechaSubida': r.FechaSubida.isoformat(),
                'DownloadUrl': f'/procesos/files/{r.Id}/download',
            }
            for r in rows
        ]
    })


@bp.route('/procesos/files', methods=['POST'])
@login_required
def procesos_upload_file():
    gestion = (request.form.get('gestion') or '').strip()
    descripcion = (request.form.get('descripcion') or '').strip()
    file = request.files.get('file')

    if not gestion:
        return jsonify({'error': 'gestion es obligatoria'}), 400

    if not file or not file.filename:
        return jsonify({'error': 'Debes adjuntar un archivo'}), 400

    if not allowed_procesos_file(file.filename):
        return jsonify({'error': 'Tipo de archivo no permitido'}), 400

    safe_original = secure_filename(file.filename)
    ext = safe_original.rsplit('.', 1)[1].lower()
    generated = f"{uuid.uuid4().hex}.{ext}"
    upload_folder = current_app.config['UPLOAD_FOLDER_PROCESOS']
    dest_path = os.path.join(upload_folder, generated)

    file.save(dest_path)
    size = os.path.getsize(dest_path)

    row = ProcesoArchivo(
        Gestion=gestion,
        Descripcion=descripcion or None,
        NombreOriginal=file.filename,
        NombreGuardado=generated,
        TipoMime=file.mimetype,
        TamanioBytes=size,
        SubidoPorDNI=session.get('dni') or '',
        SubidoPorNombre=session.get('nombre') or '',
    )
    db.session.add(row)

    registrar_bitacora(
        accion='Procesos subir archivo',
        parametros={'gestion': gestion, 'archivo': file.filename, 'size': size},
        resultado='ok',
    )
    db.session.commit()

    return jsonify({'message': 'Archivo subido correctamente', 'id': row.Id}), 201


@bp.route('/procesos/files/<int:file_id>/download', methods=['GET'])
@login_required
def procesos_download_file(file_id):
    row = ProcesoArchivo.query.get(file_id)
    if not row:
        return jsonify({'error': 'Archivo no encontrado'}), 404

    registrar_bitacora(
        accion='Procesos descargar archivo',
        parametros={'file_id': file_id, 'archivo': row.NombreOriginal},
        resultado='ok',
    )
    db.session.commit()

    return send_from_directory(
        current_app.config['UPLOAD_FOLDER_PROCESOS'],
        row.NombreGuardado,
        as_attachment=True,
        download_name=row.NombreOriginal,
    )
