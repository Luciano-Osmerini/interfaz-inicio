import os
import pyodbc
from werkzeug.security import generate_password_hash

conn_str = (
    "DRIVER={ODBC Driver 17 for SQL Server};"
    f"SERVER={os.getenv('DB_SERVER', 'localhost')};"
    f"DATABASE={os.getenv('DB_NAME', 'Usuarios')};"
    f"UID={os.getenv('DB_USER', 'sa')};"
    f"PWD={os.getenv('DB_PASSWORD', '')}"
)

usuarios = [
    {
        "Nombre": "Roberto",
        "Apellido": "Di Nolfo",
        "DNI": "23995634",
        "Rol": "Administrador",
        "Password": "Cambiar123!"
    },
    {
        "Nombre": "Luis Guillermo",
        "Apellido": "Colombo",
        "DNI": "25021525",
        "Rol": "Administrador",
        "Password": "Cambiar123!"
    }
]

try:
    conn = pyodbc.connect(conn_str)
    cursor = conn.cursor()

    cursor.execute("""
    IF OBJECT_ID('Credenciales', 'U') IS NULL
    BEGIN
        CREATE TABLE Credenciales (
            Id INT IDENTITY(1,1) PRIMARY KEY,
            DNI VARCHAR(20) NOT NULL UNIQUE,
            PasswordHash VARCHAR(255) NOT NULL,
            Activo BIT NOT NULL DEFAULT 1
        )
    END
    """)

    for u in usuarios:
        cursor.execute(
            """
            IF NOT EXISTS (SELECT 1 FROM Usuarios WHERE DNI = ?)
                INSERT INTO Usuarios (Nombre, Apellido, DNI, Rol) VALUES (?, ?, ?, ?)
            """,
            u["DNI"], u["Nombre"], u["Apellido"], u["DNI"], u["Rol"]
        )

        password_hash = generate_password_hash(u["Password"])
        cursor.execute(
            """
            IF EXISTS (SELECT 1 FROM Credenciales WHERE DNI = ?)
                UPDATE Credenciales SET PasswordHash = ?, Activo = 1 WHERE DNI = ?
            ELSE
                INSERT INTO Credenciales (DNI, PasswordHash, Activo) VALUES (?, ?, 1)
            """,
            u["DNI"], password_hash, u["DNI"], u["DNI"], password_hash
        )

    conn.commit()
    print("Usuarios y credenciales cargados correctamente.")
    print("Importante: cambia las contrasenas por defecto inmediatamente.")
except Exception as e:
    print("Error al agregar usuarios:", e)
finally:
    try:
        conn.close()
    except Exception:
        pass
