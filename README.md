# JobList API

## 1. Descripción

Backend de JobList construido con FastAPI. La implementación actual ofrece registro e inicio de sesión, tokens JWT, gestión de usuarios, autorización por roles y comprobaciones de salud. Todavía no incluye endpoints de ofertas de empleo.

La API utiliza el prefijo `/api/v1`. Al ejecutarla localmente puedes consultar:

- Swagger UI: <http://localhost:8000/docs>
- ReDoc: <http://localhost:8000/redoc>
- OpenAPI: <http://localhost:8000/openapi.json>

## 2. Tecnologías

| Componente | Tecnología |
| --- | --- |
| Lenguaje | Python 3.12, utilizado por el Dockerfile |
| API y servidor ASGI | FastAPI, Starlette y Uvicorn |
| Validación y configuración | Pydantic y pydantic-settings |
| Persistencia | PostgreSQL 16, SQLAlchemy 2 asíncrono y asyncpg |
| Migraciones | Alembic y psycopg2 |
| Autenticación | PyJWT y Argon2 |
| Límites de peticiones | SlowAPI; almacenamiento en memoria o Redis 7 |
| Logs | Loguru, salida JSON a stdout |
| Tests | pytest, pytest-asyncio, HTTPX y SQLite con aiosqlite |
| Contenedores | Docker y Docker Compose |
| Proxy de producción | Nginx con configuración HTTPS |

Las dependencias están en `requirements.txt`; las de pruebas, en `requirements-dev.txt`.

## 3. Arquitectura

Las solicitudes pasan por middlewares, rutas y dependencias de FastAPI. Los servicios contienen la lógica de negocio y los repositorios acceden a la base mediante sesiones asíncronas de SQLAlchemy.

```text
app/
  main.py                  # create_app(), routers y middlewares
  api/
    dependencies.py        # Sesión, servicios, usuario actual y roles
    routes/                # auth, users y healthy
  core/                    # Configuración, BD, JWT, logs, errores y límites
  models/                  # Modelos SQLAlchemy: User y RefreshToken
  schemas/                 # Contratos Pydantic de entrada y salida
  services/                # Lógica de autenticación y usuarios
  repositories/            # Consultas y persistencia
migrations/                # Configuración y revisiones de Alembic
  versions/                # Actualmente sin revisiones fuente
test/                     # Fixtures, integración, unit y logging
scripts/entrypoint.sh      # Migraciones y arranque de Uvicorn
nginx/nginx.conf           # Proxy HTTPS de producción
docker-compose.yml        # Servicios locales
docker-compose.prod.yml   # Servicios de producción
```

Las entidades persistidas son `users` y `refresh_token`. Los refresh tokens se vinculan al correo del usuario y a una familia de sesión.

## 4. Requisitos

- Python 3.12 y pip para ejecutar fuera de Docker.
- PostgreSQL disponible y una base creada para la aplicación.
- Docker con Compose para utilizar los servicios incluidos.
- Redis si necesitas compartir los contadores de peticiones entre procesos.
- Una clave JWT de al menos 32 caracteres.

Ejecuta los comandos desde la raíz del repositorio. Los ejemplos locales utilizan PowerShell y el intérprete de `.venv` directamente, sin activar el entorno.

## 5. Instalación local

Crea el entorno e instala las dependencias:

```powershell
py -3.12 -m venv .venv
.venv/Scripts/python.exe -m pip install -r requirements-dev.txt
```

Crea `.env` con las variables de la siguiente sección. Si utilizas la base incluida en Compose:

```powershell
docker compose up -d postgres redis
```

Prepara el esquema siguiendo la sección de migraciones **antes de iniciar la API**. El arranque directo con Uvicorn no crea tablas ni ejecuta Alembic; el contenedor sí ejecuta las revisiones existentes antes de iniciar Uvicorn.

Para utilizar Redis localmente, exporta su URL al proceso; `app/core/rate_limit.py` la obtiene mediante `os.getenv`, no desde el objeto de configuración que lee `.env`:

```powershell
$env:REDIS_URL = "redis://localhost:6379/0"
.venv/Scripts/python.exe -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

En Linux/macOS, sustituye `.venv/Scripts/python.exe` por `.venv/bin/python` y crea el entorno con `python3.12 -m venv .venv`.

## 6. Variables de entorno

Ejemplo de `.env` para la API local y PostgreSQL de Compose. Sustituye los valores de ejemplo antes de usarlo:

```dotenv
PROJECT_NAME="Job List"
ENVIROMENT=development
DEBUG=true
PORT=8000

DB_HOST=localhost
DB_PORT=5433
DB_NAME=joblist
DB_USER=postgres
DB_PASSWORD=replace_with_local_password

JWT_SECRET_KEY=replace_with_a_random_secret_of_at_least_32_characters
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=60
REFRESH_TOKEN_EXPIRE_DAYS=7

ALLOWED_ORIGINS='["http://localhost:3000","http://localhost:5173"]'
DB_POOL_SIZE=20
DB_MAX_OVERFLOW=10
DB_POOL_TIMEOUT=30
DB_POOL_RECYCLE=1800
DB_ECHO=false
REDIS_URL=redis://localhost:6379/0
```

| Variable | Obligatoria / valor predeterminado | Uso |
| --- | --- | --- |
| `DB_HOST`, `DB_PORT`, `DB_NAME`, `DB_USER`, `DB_PASSWORD` | Obligatorias | Construcción de la conexión PostgreSQL con asyncpg |
| `JWT_SECRET_KEY` | Obligatoria, mínimo 32 caracteres | Firma y validación JWT |
| `JWT_ALGORITHM` | `HS256` | Algoritmo JWT |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | `60` | Duración del access token |
| `REFRESH_TOKEN_EXPIRE_DAYS` | `7` | Duración del refresh token |
| `ALLOWED_ORIGINS` | Los dos orígenes locales del ejemplo | Lista JSON para CORS, no texto separado por comas |
| `PROJECT_NAME` | `Job List` | Título de FastAPI |
| `ENVIROMENT` | `development` | Nombre exacto declarado en el código, incluida su escritura |
| `DEBUG` | `true` | Booleano de configuración; no activa por sí solo un modo de despliegue |
| `PORT` | `8000` | Valor de configuración; Uvicorn usa el puerto indicado en su comando |
| `DB_POOL_SIZE`, `DB_MAX_OVERFLOW` | `20`, `10` | Tamaño y conexiones adicionales del pool |
| `DB_POOL_TIMEOUT`, `DB_POOL_RECYCLE` | `30`, `1800` segundos | Espera y reciclaje de conexiones |
| `DB_ECHO` | `false` | Declarada; el motor mantiene `echo=False` explícitamente |
| `REDIS_URL` | `memory://` | SlowAPI la lee del entorno del proceso |

Los nombres distinguen mayúsculas y minúsculas. Las variables exportadas al proceso prevalecen sobre `.env`. Tanto `.env` como `.env.production` están excluidos de Git. La aplicación lee `.env` por defecto; en producción, Compose inyecta `.env.production` al proceso mediante `env_file`. Puedes generar una clave con:

```powershell
.venv/Scripts/python.exe -c "import secrets; print(secrets.token_urlsafe(48))"
```

## 7. Docker

Compose define estos servicios y puertos:

| Servicio | Puerto del equipo → contenedor | Persistencia |
| --- | --- | --- |
| `api` | `8000 → 8000` | Imagen construida con el Dockerfile |
| `postgres` | `5433 → 5432` | Volumen `postgres_data` |
| `redis` | `6379 → 6379` | Volumen `redis_data` |

Dentro de la red de Compose, la API usa `postgres:5432` y Redis debe usar `redis:6379`.

Antes de desplegar, agrega estas entradas a `services.api.environment` en `docker-compose.yml`:

```yaml
JWT_SECRET_KEY: ${JWT_SECRET_KEY:?Define JWT_SECRET_KEY en .env}
REDIS_URL: redis://redis:6379/0
```

Define `ALLOWED_ORIGINS` como JSON en `.env`: el valor predeterminado separado por comas del Compose actual no coincide con el tipo esperado por Pydantic. Compose no inyecta automáticamente todas las variables de `.env` al contenedor; agrega también las demás opciones que quieras personalizar.

El Dockerfile actual usa `COPY . .` y no hay `.dockerignore`. Antes de construir, crea este archivo para excluir al menos `.env`, `.env.*`, `.git`, `.venv`, `venv`, `__pycache__`, `.pytest_cache` y `*.log`; proporciona los secretos mediante el entorno.

La imagen utiliza dos etapas de construcción e inicia como usuario sin privilegios (`appuser`). `scripts/entrypoint.sh` ejecuta `alembic upgrade head` y, si termina correctamente, inicia Uvicorn en el puerto 8000 con cuatro workers, sin recarga y sin access log de Uvicorn. Los logs JSON de la aplicación permanecen activos.

Compose espera a que PostgreSQL y Redis estén saludables. El script no implementa un bucle de espera propio: si Alembic falla, termina el contenedor y se aplica la política de reinicio.

Después de preparar las revisiones del esquema:

```powershell
docker compose up -d --build
docker compose ps
docker compose logs -f api
```

Para detener los servicios sin borrar los volúmenes:

```powershell
docker compose down
```

## 8. Migraciones

Alembic utiliza las mismas variables `DB_*` que la API. La API conecta con asyncpg y las migraciones con psycopg2, incluido en `requirements.txt`. Las URLs se construyen con SQLAlchemy para admitir caracteres especiales en las credenciales. Ya no debes configurar una URL independiente en `alembic.ini`.

| Ejecución | `DB_HOST` | `DB_PORT` |
| --- | --- | --- |
| Python local y PostgreSQL de Compose | `localhost` | `5433` |
| API dentro de Compose | `postgres` | `5432` |

Dentro del contenedor, `localhost` apunta al propio contenedor de la API, no al servicio PostgreSQL.

`migrations/env.py` registra los modelos `User` y `RefreshToken`. Sin embargo, `migrations/versions/` todavía no contiene revisiones fuente: ejecutar `upgrade head` no crea por sí solo las tablas de la aplicación.

Para preparar la primera revisión, utiliza una base vacía de desarrollo y las variables locales correctas:

```powershell
.venv/Scripts/python.exe -m alembic revision --autogenerate -m "initial schema"
```

Revisa que la revisión incluya las tablas, índices, enum y claves foráneas esperados. Después aplícala y guarda el archivo en Git:

```powershell
.venv/Scripts/python.exe -m alembic upgrade head
.venv/Scripts/python.exe -m alembic current
.venv/Scripts/python.exe -m alembic history
```

Para cambios posteriores, modifica los modelos y genera una nueva revisión. Autogenerar contra una base que ya contiene las tablas puede producir una revisión vacía: no la uses como esquema inicial para instalaciones nuevas.

En Docker, el entrypoint aplica automáticamente las revisiones incluidas en la imagen antes de iniciar Uvicorn. También puedes consultar el estado de la base sin iniciar la API:

```powershell
docker compose run --rm --no-deps --entrypoint python api -m alembic current
```

Este último comando requiere la imagen construida y PostgreSQL iniciado. No generes revisiones automáticamente en producción; despliega archivos revisados y respalda la base antes de aplicar cambios.

## 9. Tests

```powershell
.venv/Scripts/python.exe -m pip install -r requirements-dev.txt
.venv/Scripts/python.exe -m pytest -q -p no:cacheprovider
```

Puedes ejecutar un archivo concreto:

```powershell
.venv/Scripts/python.exe -m pytest test/test_logging.py -v -p no:cacheprovider
.venv/Scripts/python.exe -m pytest test/integration/test_auth.py -v -p no:cacheprovider
```

Los fixtures crean SQLite en memoria por test, sustituyen la dependencia de sesión y usan almacenamiento en memoria para SlowAPI. Configuran valores de prueba independientes de las credenciales de `.env`. HTTPX llama directamente a la aplicación ASGI, sin abrir un servidor.

La suite comprueba autenticación, revocación tras logout, permisos, paginación, actualización, validación, correos duplicados, logging y configuración de Alembic (modos online y offline). No sustituye las pruebas de migraciones, PostgreSQL, Redis o despliegue Docker. `-p no:cacheprovider` evita escribir la caché de pytest.

## 10. Endpoints

Todas las rutas siguientes llevan el prefijo `/api/v1`:

| Método | Ruta | Acceso actual | Resultado exitoso |
| --- | --- | --- | --- |
| POST | `/auth/register` | Público, 3/hora por IP | `201`, usuario creado |
| POST | `/auth/login` | Público, 5/minuto por IP | `200`, access y refresh tokens |
| POST | `/auth/refresh` | Refresh token en JSON, 10/minuto por IP | `200`, nuevos tokens |
| POST | `/auth/logout` | Refresh token en JSON | `200`, revocación del token |
| POST | `/users` | Público | `201` declarado; ver limitación inferior |
| GET | `/users/me` | `user` o `admin` activo | `200`, perfil propio |
| GET | `/users` | `admin` activo | `200`, usuarios paginados |
| GET | `/users/{id}` | Solo `user` activo | `200`, usuario solicitado |
| PATCH | `/users/{user_id}` | `admin` activo | `200`, usuario actualizado |
| DELETE | `/users/{user_id}` | `admin` activo | `204`, sin cuerpo |
| GET | `/health` | Público | `200`, proceso disponible |
| GET | `/health/ready` | Público | `200` con BD accesible; `503` si falla |

`GET /users` acepta `limit` entre 1 y 100 (20 por defecto) y `offset` desde 0 (0 por defecto). Devuelve `items`, `total`, `limit` y `offset`.

El registro requiere `email`, `password`, `firstname` y `lastname`. Actualmente `PATCH` también exige `firstname` y `lastname`, aunque los demás campos son opcionales.

La ruta pública `POST /users` sigue un servicio distinto que no asigna los nombres obligatorios al modelo: usa `/auth/register` para registrar usuarios hasta corregir esa ruta. `/health/ready` solo comprueba una conexión con `SELECT 1`; no valida tablas ni Redis.

## 11. Autenticación

Registra una cuenta enviando JSON a `/api/v1/auth/register`:

```json
{
  "email": "persona@example.com",
  "password": "ExamplePassword123!",
  "firstname": "Ana",
  "lastname": "Perez"
}
```

Inicia sesión con `application/x-www-form-urlencoded`. El campo OAuth2 se llama `username`, pero su valor es el correo:

```powershell
$session = Invoke-RestMethod -Method Post -Uri "http://localhost:8000/api/v1/auth/login" -ContentType "application/x-www-form-urlencoded" -Body @{ username = "persona@example.com"; password = "ExamplePassword123!" }
Invoke-RestMethod -Uri "http://localhost:8000/api/v1/users/me" -Headers @{ Authorization = "Bearer $($session.access_token)" }
```

Los JWT contienen `sub` con el **correo**, `type`, `iat` y `exp`. Las rutas protegidas esperan `Authorization: Bearer <access_token>`; el rol se consulta en la base de datos.

Para renovar o cerrar sesión, envía a `/auth/refresh` o `/auth/logout`:

```json
{"refresh_token": "<refresh_token_recibido>"}
```

La renovación marca el token anterior como usado y revocado, y emite otro dentro de la misma familia. Si se reutiliza uno usado o revocado, se revoca su familia. Se almacena el hash SHA-256 del refresh token, no su valor original.

Logout revoca el refresh token enviado. El access token emitido sigue siendo válido hasta expirar; no existe una lista de revocación de access tokens.

## 12. Roles

| Rol | Permisos actuales |
| --- | --- |
| `user` | Consultar su perfil y consultar usuarios por ID |
| `admin` | Consultar su perfil, listar, actualizar y eliminar usuarios |

El registro público crea siempre un usuario con rol `user`. No existe un comando de bootstrap del primer administrador: su asignación inicial requiere una operación administrativa controlada en la base de datos. Un administrador existente puede modificar `role` mediante `PATCH /users/{user_id}`.

Los permisos no son jerárquicos: actualmente `admin` no está incluido en `GET /users/{id}`. Esa ruta tampoco limita al usuario a consultar su propio ID. Una cuenta inactiva no puede iniciar sesión ni acceder a las rutas protegidas por usuario activo.

## 13. Seguridad

La [auditoría de seguridad](SECURITY_AUDIT.md) del 10 de septiembre de 2026 documenta los 24 controles, hallazgos pendientes y pruebas reproducibles. El resultado actual no aprueba el despliegue de producción.

Las contraseñas se almacenan con Argon2. El registro valida un mínimo de ocho caracteres con mayúscula, minúscula y número; esta política no se aplica actualmente al campo `password` de actualización.

La API valida firma, expiración y tipo de JWT, comprueba el usuario y aplica autorización por rol. SlowAPI limita registro, login y refresh, devolviendo `429` al superar el límite. Su configuración declara además un límite predeterminado de 100/minuto; no debe asumirse protección global de todas las rutas, ya que la aplicación no instala `SlowAPIMiddleware`.

Se incluyen las cabeceras `X-Content-Type-Options: nosniff`, `X-Frame-Options: DENY` y `Referrer-Policy: strict-origin-when-cross-origin`. CORS utiliza los orígenes configurados y permite credenciales. Actualmente su lista de métodos omite `PATCH`, por lo que las actualizaciones desde un frontend de otro origen requieren corregir esa lista.

Los logs estructurados salen a stdout con `timestamp`, `level`, `message`, `correlation_id`, `module` y `data`. Un `X-Request-ID` válido se reutiliza; si falta o es inválido, se genera un UUID y se devuelve también en respuestas de error.

Los eventos de solicitud registran método, plantilla de ruta, estado y duración. Los eventos administrativos incorporan identificadores del actor y del objetivo. La configuración redacta campos sensibles y tokens, desactiva SQL echo y evita incluir detalles de excepciones en la salida estructurada.

Para agregar eventos, utiliza mensajes constantes y metadatos controlados:

```python
logger.info("user_updated", event="admin.user_updated", actor_id=str(actor.id))
```

No interpolar contraseñas, tokens, SQL o excepciones completas. La redacción es una defensa adicional: el health check de readiness aún construye un mensaje con el texto de la excepción y conviene sustituirlo por un evento constante.

## 14. Producción

`docker-compose.prod.yml` define API, PostgreSQL, Redis y Nginx. Utilízalo como archivo independiente con `-f`; la API y las bases no publican puertos al host en este archivo, y Nginx expone 80 y 443. Incluye límites de recursos y volúmenes para datos y certificados.

Prepara `.env.production` con las variables de la sección 6 y estos valores específicos. Los valores siguientes son ejemplos, no credenciales válidas de despliegue:

```dotenv
ENVIROMENT=production
DEBUG=false
DB_HOST=postgres
DB_PORT=5432
DB_USER=joblist
DB_PASSWORD=replace_with_production_password
DB_NAME=joblist
POSTGRES_USER=joblist
POSTGRES_PASSWORD=replace_with_production_password
POSTGRES_DB=joblist
JWT_SECRET_KEY=replace_with_a_generated_random_secret
REDIS_URL=redis://redis:6379/0
ALLOWED_ORIGINS='["https://app.example.com"]'
```

`DB_USER`, `DB_PASSWORD` y `DB_NAME` deben coincidir con `POSTGRES_USER`, `POSTGRES_PASSWORD` y `POSTGRES_DB`: el archivo de producción usa los primeros para la API y los segundos para inicializar PostgreSQL. Cambiar estas variables no actualiza las credenciales de una base que ya tiene datos en el volumen.

`env_file: .env.production` inyecta variables en la API; `--env-file .env.production` proporciona además los valores de interpolación `${POSTGRES_*}` al comando Compose. Se necesitan ambas funciones para esta configuración.

Antes del primer despliegue, completa estos ajustes existentes en los archivos:

1. Crea `.dockerignore` como se indica en la sección Docker para excluir secretos y entornos locales de la imagen.
2. Corrige el health check de `api` en `docker-compose.prod.yml`: `/health/liveness` no existe. Utiliza `curl -f http://localhost:8000/api/v1/health/ready` para comprobar la conexión a PostgreSQL, o `/api/v1/health` para comprobar solo el proceso.
3. Sustituye `tudominio.com` en `nginx/nginx.conf` por tu dominio y proporciona los certificados en las rutas configuradas. Nginx no arrancará con certificados ausentes. Los volúmenes `certbot_certs` y `certbot_www` no emiten ni renuevan certificados automáticamente: el Compose actual no incluye un servicio Certbot.
4. Incluye revisiones de Alembic revisadas en la imagen. El entrypoint las ejecutará antes de Uvicorn; coordina este paso si despliegas varias réplicas para evitar migraciones concurrentes.

Una vez completados esos preparativos, valida y levanta los servicios:

```powershell
docker compose --env-file .env.production -f docker-compose.prod.yml config --quiet
docker compose --env-file .env.production -f docker-compose.prod.yml up -d --build
docker compose --env-file .env.production -f docker-compose.prod.yml ps
docker compose --env-file .env.production -f docker-compose.prod.yml logs -f api nginx
```

Para detenerlos conservando sus volúmenes:

```powershell
docker compose --env-file .env.production -f docker-compose.prod.yml down
```

Ajusta los cuatro workers de `scripts/entrypoint.sh` y el pool de conexiones a los recursos disponibles. Cada proceso tiene su propio pool; utiliza Redis compartido para mantener los contadores de peticiones entre procesos. Recopila los logs de stdout y prepara respaldos y recuperación de PostgreSQL.

Nginx configura HTTPS y HSTS, pero debes restringir los proxies confiables de la API: actualmente se confía en `*`. Completa también los ajustes de CORS, permisos por ID, registro duplicado y validación de contraseña descritos en las secciones de endpoints y seguridad.

`DEBUG=false` y `ENVIROMENT=production` no deshabilitan Swagger/ReDoc ni activan automáticamente HTTPS o HSTS en FastAPI. La configuración del proxy y los certificados debe estar lista antes de exponer el servicio.
