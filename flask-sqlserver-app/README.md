# Proyecto Atento - Flask + SQL Server

Aplicacion web para autenticacion, gestion de usuarios y operaciones internas sobre procesos, con backend en Flask y persistencia en SQL Server.

## Problema que resuelve

Permite centralizar acceso por rol, registrar actividad operativa y habilitar flujos internos (asesores, estructura, procesos) con trazabilidad.

## Stack tecnico

- Backend: Flask + SQLAlchemy
- Base de datos: SQL Server (pyodbc)
- Seguridad: hash de password, sesion por cookie, control por roles
- Frontend: HTML, CSS y JavaScript vanilla

## Funcionalidades principales

- Login y logout por sesion
- Registro de cuenta publica controlada
- Cambio de password autenticado
- Gestion de usuarios por superadmin
- Bitacora de acciones con filtros
- Carga y descarga de archivos de procesos

## Arquitectura (resumen)

- Frontend estatico: pantallas en carpetas de interfaz
- API Flask: autenticacion, usuarios, bitacora y archivos
- SQL Server: usuarios, credenciales, gestiones y bitacora

## Requisitos

- Python 3.10 o superior
- SQL Server accesible
- ODBC Driver 17 u 18 para SQL Server

## Instalacion local

1. Entrar a la carpeta del backend:

```bash
cd flask-sqlserver-app
```

2. Crear e iniciar entorno virtual:

```bash
python -m venv venv
venv\Scripts\activate
```

3. Instalar dependencias:

```bash
pip install -r requirements.txt
```

## Configuracion

1. Crear archivo .env basado en .env.example.
2. Completar credenciales reales de base de datos y claves de seguridad.

Variables principales:

- DB_SERVER
- DB_NAME
- DB_USER
- DB_PASSWORD
- DB_DRIVER
- SECRET_KEY
- SESSION_COOKIE_SECURE
- ADMIN_BOOTSTRAP_TOKEN
- SUPERADMIN_DNI

## Inicializacion de usuarios y credenciales

Para crear/actualizar usuarios base y su tabla de credenciales:

```bash
python app/agregar_usuarios.py
```

## Ejecucion

```bash
python run.py
```

API disponible en http://127.0.0.1:5000.

## Endpoints relevantes

- POST /auth/login
- POST /auth/logout
- GET /auth/me
- POST /auth/signup
- POST /auth/change-password
- POST /auth/register
- GET /admin/users
- PATCH /admin/users/<id>
- GET /admin/bitacora
- GET/POST /procesos/files
- GET /procesos/files/<id>/download

## Seguridad implementada

- Passwords con hash (werkzeug.security)
- Sesion con cookie HttpOnly y SameSite=Lax
- Timeout de sesion configurable
- Variables sensibles por entorno (.env)
- Rutas protegidas por autenticacion y rol

## Recomendaciones antes de produccion

- Cambiar passwords por defecto de usuarios semilla
- Definir SECRET_KEY fuerte
- Activar SESSION_COOKIE_SECURE=true en HTTPS
- Configurar rotacion y respaldo de logs

## Material para publicacion en LinkedIn

Para facilitar tu publicacion, revisa estos archivos en la raiz del proyecto:

- LINKEDIN_POST.md
- MEJORAS_PRIORIZADAS.md
