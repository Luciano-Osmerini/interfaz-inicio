import pyodbc

conn_str = (
    "DRIVER={ODBC Driver 17 for SQL Server};"
    "SERVER=CB1SB04EA\\SQLEXPRESS01;"
    "DATABASE=Usuarios;"
    "UID=rpa_clientes_writer;"
    "PWD=Luciano1707*"
)

try:
    conn = pyodbc.connect(conn_str)
    cursor = conn.cursor()
    cursor.execute("SELECT TOP 1 * FROM Usuarios")
    row = cursor.fetchone()
    if row:
        print("Primer usuario:", row)
    else:
        print("No hay usuarios en la tabla.")
    conn.close()
except Exception as e:
    print("Error de conexión:", e)