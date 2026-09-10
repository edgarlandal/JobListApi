
### Logging estructurado

La API escribe una linea JSON por evento a stdout al iniciar con `uvicorn app.main:app`.
Incluye timestamp UTC, level, message, correlation_id, module y data.

- Envia `X-Request-ID` con un UUID para reutilizarlo; si falta o es invalido, se genera uno.
- La respuesta devuelve `X-Request-ID`, tambien en errores 500 y accesible por CORS.
- Eventos: `request.started`, `request.completed`, `request.failed`, `auth.*` y `admin.*`.
- Los eventos administrativos exitosos incluyen actor_id y, en cambios/eliminaciones, target_id.
- Las requests registran la plantilla de ruta y duracion, nunca query strings, cuerpos ni cabeceras.
- Los errores conservan su tipo, sin mensaje, SQL, variables locales o traceback que puedan exponer credenciales.
- SQL echo queda desactivado. Los mensajes de librerias externas se sustituyen por `external_log`, conservando origen y nivel.

Para agregar eventos usa mensajes constantes y metadatos controlados, por ejemplo:
`logger.info("user_updated", event="admin.user_updated", actor_id=str(actor.id))`.
No interpolar passwords, tokens, secrets ni objetos completos: la redaccion de campos sensibles
anidados y JWT es una defensa adicional, no un detector de cualquier secreto en texto libre.

### Pruebas

Instala las dependencias y ejecuta toda la suite (integracion y logging):

```powershell
.venv/Scripts/python.exe -m pip install -r requirements-dev.txt
.venv/Scripts/python.exe -m pytest -q -p no:cacheprovider
```

Los fixtures crean una base SQLite en memoria por test y usan Redis en memoria.
No conectan a la base de `.env` ni ejecutan el startup de la aplicacion.
Estas pruebas no sustituyen la validacion de migraciones y comportamiento especifico de PostgreSQL.
El aviso de FastAPI sobre `on_event` corresponde al startup existente.
