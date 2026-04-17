import os
from urllib.parse import quote_plus

from dotenv import load_dotenv


load_dotenv()


class Config:
    BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))

    DB_SERVER  = os.getenv("DB_SERVER",  ".\\SQLEXPRESS")
    DB_NAME    = os.getenv("DB_NAME",    "Usuarios")
    DB_DRIVER  = os.getenv("DB_DRIVER",  "ODBC Driver 18 for SQL Server")
    DB_TRUSTED = os.getenv("DB_TRUSTED", "yes")

    # Si DB_TRUSTED=yes usa autenticacion de Windows (sin usuario/password)
    # Si DB_TRUSTED=no usa usuario y password SQL
    DB_USER     = os.getenv("DB_USER",     "")
    DB_PASSWORD = os.getenv("DB_PASSWORD", "")

    if DB_TRUSTED.lower() == "yes":
        SQLALCHEMY_DATABASE_URI = (
            f"mssql+pyodbc://{DB_SERVER}/{DB_NAME}"
            f"?driver={quote_plus(DB_DRIVER)}"
            f"&trusted_connection=yes&TrustServerCertificate=yes"
        )
    else:
        SQLALCHEMY_DATABASE_URI = (
            "mssql+pyodbc://"
            f"{quote_plus(DB_USER)}:{quote_plus(DB_PASSWORD)}@"
            f"{DB_SERVER}/{DB_NAME}?driver={quote_plus(DB_DRIVER)}"
            f"&TrustServerCertificate=yes"
        )
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    SECRET_KEY = os.getenv("SECRET_KEY", "change-this-secret-key")
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = "Lax"
    SESSION_COOKIE_SECURE = os.getenv("SESSION_COOKIE_SECURE", "false").lower() == "true"
    SESSION_TIMEOUT_MINUTES = int(os.getenv("SESSION_TIMEOUT_MINUTES", "30"))

    _default_origins = [
        'http://localhost:5500',
        'http://127.0.0.1:5500',
        'http://localhost:5501',
        'http://127.0.0.1:5501',
        'http://localhost:5000',
        'http://127.0.0.1:5000',
        'https://luciano-osmerini.github.io',
    ]
    _cors_origins_raw = os.getenv('CORS_ORIGINS', ','.join(_default_origins))
    CORS_ORIGINS = [origin.strip() for origin in _cors_origins_raw.split(',') if origin.strip()]
    ALLOW_NULL_ORIGIN = os.getenv('ALLOW_NULL_ORIGIN', 'false').lower() == 'true'

    UPLOAD_FOLDER_PROCESOS = os.getenv(
        "UPLOAD_FOLDER_PROCESOS",
        os.path.join(BASE_DIR, 'uploads', 'procesos')
    )
    MAX_CONTENT_LENGTH = int(os.getenv("MAX_CONTENT_LENGTH", str(25 * 1024 * 1024)))
