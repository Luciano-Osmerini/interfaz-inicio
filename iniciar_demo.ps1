$backendPath = "c:/Users/user/Desktop/AA-Proyecto Atento/Interfaz/Proyecto/Proyecto atento/flask-sqlserver-app"
$pythonExe = "$backendPath/.venv/Scripts/python.exe"
$frontendIndex = "c:/Users/user/Desktop/AA-Proyecto Atento/Interfaz/Proyecto/Proyecto atento/Interfaz Inicio/Interfaz Inicio/index.html"

Start-Process powershell -ArgumentList "-NoExit", "-Command", "Set-Location '$backendPath'; & '$pythonExe' run.py"
Start-Process $frontendIndex
