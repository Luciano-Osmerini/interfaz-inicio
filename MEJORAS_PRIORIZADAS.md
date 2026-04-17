# Mejoras priorizadas antes de publicar

## Prioridad alta (hacer primero)
1. Demo publica funcionando
- Publicar una URL accesible (render, railway, azure o similar).
- Mostrar login, cambio de clave y flujo de procesos.

2. Evidencia visual profesional
- Grabar video corto de 45-60 segundos.
- Preparar capturas limpias de las pantallas clave.

3. Narrativa de producto
- Explicar problema, solucion y valor de negocio.
- Definir quien usa la app y para que.

4. Hardening basico
- Revisar CORS para dominio de frontend.
- Definir SECRET_KEY y variables productivas.
- Confirmar limites de subida y extensiones permitidas.

## Prioridad media (te diferencia)
1. Medicion de uso
- Agregar contadores de operaciones y tiempos de respuesta.
- Mostrar metricas en tablero simple.

2. UX y estados de error
- Mensajes consistentes para errores de red y sesion.
- Estados vacios en tablas y carga de archivos.

3. Calidad tecnica
- Agregar pruebas basicas de endpoints criticos.
- Incorporar validaciones adicionales en signup y carga de archivos.

## Prioridad baja (iteracion)
1. Docker para ejecucion reproducible.
2. Pipeline simple de CI para lint/test.
3. Documentacion de despliegue por ambiente.

## Checklist de publicacion en LinkedIn
- README actualizado con stack y funcionalidades.
- URL de demo o video funcional.
- Post breve con resultado y aprendizaje.
- Enlace al repositorio y llamada a feedback.
