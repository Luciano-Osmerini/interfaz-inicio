# Guia rapida para grabar demo (LinkedIn)

## Objetivo
Grabar un video de 45-60 segundos mostrando que la app funciona de punta a punta.

## Formato recomendado
- Resolucion: 1920x1080
- FPS: 30
- Duracion final: 45-60 segundos
- Audio: opcional (puedes subirlo sin voz y con texto en pantalla)

## Opcion 1 (mas rapida): Xbox Game Bar (Windows)
1. Abre la app en pantalla.
2. Presiona Win + G.
3. En Capturar, presiona Iniciar grabacion (o Win + Alt + R).
4. Repite Win + Alt + R para detener.
5. El video queda en Videos/Captures.

## Opcion 2: OBS Studio
1. Crea una escena nueva llamada Demo App.
2. Agrega fuente Captura de ventana (tu navegador).
3. Configura salida a 1080p 30fps.
4. Inicia grabacion, ejecuta el flujo, detiene y exporta.

## Flujo exacto de demo (guion de 60 segundos)
0-5s:
- Mostrar pantalla de inicio y titulo de la solucion.

5-20s:
- Iniciar sesion con un usuario valido.
- Mostrar bienvenida y rol.

20-35s:
- Ir a Gestion de usuarios (si eres superadmin).
- Mostrar que puedes listar/editar usuario o filtrar bitacora.

35-50s:
- Ir a Procesos y mostrar carga/listado de archivo.

50-60s:
- Volver al inicio y cerrar sesion.
- Cierre visual con texto: Flask + SQL Server + seguridad por roles.

## Texto corto para sobreimpresion (opcional)
- Autenticacion y control por roles
- Gestion de usuarios y bitacora
- Carga y gestion de procesos
- Backend Flask + SQL Server

## Checklist antes de grabar
- API levantada en http://127.0.0.1:5000
- Frontend abierto en navegador
- Usuario de prueba listo
- Datos de ejemplo cargados
- Notificaciones del sistema desactivadas

## Comandos utiles para iniciar backend
En PowerShell, dentro de flask-sqlserver-app:

```powershell
& "c:/Users/user/Desktop/AA-Proyecto Atento/Interfaz/Proyecto/Proyecto atento/flask-sqlserver-app/.venv/Scripts/python.exe" run.py
```

## Edicion minima para LinkedIn
- Recorta silencios (inicio/fin).
- Agrega portada con titulo del proyecto.
- Exporta en MP4 (H.264).
- Sube junto con 2-3 capturas y descripcion breve.
