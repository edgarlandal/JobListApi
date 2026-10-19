# JobList API

API con FastAPI, PostgreSQL y SQLAlchemy para autenticación, usuarios y seguimiento de postulaciones. Esta es la única guía del proyecto. Ejecuta los comandos desde la raíz en PowerShell.

## Comandos de uso habitual

Ejecuta estos comandos desde la raíz del proyecto en PowerShell, con Docker Desktop iniciado.

```powershell
# Validar la configuración y levantar la aplicación
docker compose config --quiet
docker compose up -d --build

# Consultar servicios y logs
docker compose ps -a
docker compose logs --tail 50 api

# Consultar el estado de las migraciones (no modifican la BD)
docker compose run --rm migrate current
docker compose run --rm migrate heads
docker compose run --rm migrate history
docker compose run --rm migrate check

# Comprobar dependencias y pruebas locales
.venv/Scripts/python.exe -m pip check
.venv/Scripts/python.exe -m pytest test/test_logging.py test/unit/test_migration_config.py -q -p no:cacheprovider
```

- Documentación interactiva: <http://localhost:8000/docs>.
- Salud del proceso: <http://localhost:8000/api/v1/health>.
- Conexión a PostgreSQL: <http://localhost:8000/api/v1/health/ready>.

Los checks de salud no prueban todos los endpoints. El servicio `api` usa el código de la imagen: los cambios en `app/` requieren reconstruir y recrear la API con `docker compose up -d --build api`. El servicio `migrate` monta los modelos locales para detectar cambios sin reconstruir por cada edición de un modelo.

Los comandos de esta edición se ajustaron al Compose adjunto y al diagnóstico de migraciones. No se ejecutaron contra tu Docker Desktop ni se volvió a correr la suite del proyecto.

## Suite completa: hay fallos pendientes

```powershell
.venv/Scripts/python.exe -m pytest -q -p no:cacheprovider
```

Resultado histórico documentado al revisar el código local (no repetido en esta edición): **8 aprobadas, 1 fallo y 11 errores**. SQLAlchemy no encuentra `UserSkill` al configurar las relaciones; el manejador de errores también intenta acceder a `exc.orig` en una excepción que no tiene ese atributo. Estos problemas ya estaban presentes antes de la limpieza.

Las pruebas usan SQLite en memoria y configuración de prueba; no modifican PostgreSQL. Las 7 pruebas aprobadas del bloque anterior cubren solo logging y configuración de migraciones, no toda la API.

## Arranque y configuración

Se necesitan Docker Desktop con Compose, o Python 3.12 y PostgreSQL para ejecución local. Conserva `requirements.txt` (aplicación) y `requirements-dev.txt` (incluye aplicación y pruebas). Los ejemplos locales usan `.venv`; si tu entorno se llama `venv`, ajusta esa ruta.

Para una instalación nueva, crea `.venv` con `py -3.12 -m venv .venv` e instala `requirements-dev.txt` con `.venv/Scripts/python.exe -m pip install -r requirements-dev.txt`. No se reinstalaron dependencias durante esta limpieza.

La configuración privada está en `.env`. Variables mínimas:

```dotenv
DB_HOST=localhost
DB_PORT=5433
DB_NAME=joblist
DB_USER=postgres
DB_PASSWORD=reemplazar_por_tu_password
JWT_SECRET_KEY=reemplazar_por_una_clave_aleatoria_de_al_menos_32_caracteres
ALLOWED_ORIGINS='["http://localhost:3000","http://localhost:5173"]'
```

Compose carga `.env` y sustituye el host y puerto de la API por `postgres:5432`. PostgreSQL se publica en `localhost:5433`; la API, en `localhost:8000`. Para compartir los límites de peticiones entre los workers del contenedor, configura `REDIS_URL=redis://redis:6379/0` en `.env`. Fuera de Docker, SlowAPI lee `REDIS_URL` del entorno del proceso y usa memoria si no está definida.

El comando habitual de arranque es `docker compose up -d --build`. Según la configuración previamente documentada, el entrypoint de la API aplica las migraciones antes de iniciar Uvicorn; no genera archivos nuevos. El servicio `migrate` ejecuta Alembic directamente, sin pasar por ese entrypoint. Para detener los servicios conservando los datos, usa `docker compose down`, sin `-v`.

## Migraciones

Crear o editar un modelo SQLAlchemy no crea ni aplica una migración automáticamente. Alembic compara los modelos registrados con la base configurada al usar `revision --autogenerate`.

### Configuración de Compose

El servicio `migrate` comparte imagen, configuración de base de datos y red con la API. Espera a que `postgres` esté saludable y tiene `entrypoint: ["alembic"]`. Su perfil `tools` evita que se inicie con el arranque habitual; al solicitarlo explícitamente con `docker compose run`, no necesitas activar el perfil.

Los volúmenes están definidos en Compose:

- `./app:/app/app:ro`: lee los modelos locales actualizados.
- `./migrations:/app/migrations`: conserva los archivos generados en Windows.
- `./alembic.ini:/app/alembic.ini:ro`: lee la configuración local de Alembic.

La API también monta `./migrations:/app/migrations` para ver el historial actualizado. Conserva esos archivos y registra las migraciones en Git junto con los modelos. Estos montajes son para el entorno de desarrollo.

### Generar, revisar y aplicar

Para la primera ejecución, construye la imagen compartida:

```powershell
docker compose build api
```

Antes de generar, importa todos los modelos desde `app/models/__init__.py` o desde `migrations/env.py`. Deben usar la misma `Base`, y `env.py` debe configurar `target_metadata = Base.metadata`. Mantén cargados también los modelos existentes: un metadata incompleto puede proponer eliminar tablas.

```powershell
# 1. Consultar la versión aplicada y el historial
docker compose run --rm migrate current
docker compose run --rm migrate history

# 2. Generar un archivo con los cambios detectados
docker compose run --rm migrate revision --autogenerate -m "add skills"

# 3. Ver los archivos generados en Windows
Get-ChildItem .\migrations\versions
```

Abre el nuevo archivo y revisa `upgrade()` y `downgrade()` antes de aplicarlo. Para las tablas nuevas, espera instrucciones `op.create_table(...)`; un `upgrade()` con solo `pass` no crea tablas. Revisa también cualquier operación de eliminación inesperada.

```powershell
# 4. Aplicar las migraciones pendientes
docker compose run --rm migrate upgrade head

# 5. Confirmar la versión aplicada y las diferencias de esquema
docker compose run --rm migrate current
docker compose run --rm migrate check
```

No necesitas `--no-deps`, `--entrypoint` ni un volumen `-v` en estos comandos. Compose espera a PostgreSQL y conserva la migración en la carpeta local. Eliminar el contenedor temporal con `--rm` no elimina esos archivos ni el volumen de PostgreSQL.

### Historial de skills y errores encontrados

- `68720f2b3f81`: revisión inicial de usuarios, postulaciones y refresh tokens.
- `b4af43a1a35b`: `add_skills_models` vacía, ya registrada como aplicada durante el diagnóstico.
- `8c03adbb06ba`: nueva migración `add_skills_models`. Inicialmente falló porque `job_skills.minimum_level` estaba definido como UUID. Se indicó corregirlo a entero en el modelo y en el archivo de migración. El usuario informó que después dejó de dar error; confirma las tablas y la revisión con los comandos anteriores.

`UserSkill.level` y `JobSkill.minimum_level` deben ser enteros para validar `BETWEEN 1 AND 3`. Los identificadores `user_id`, `job_id` y `skill_id` siguen siendo UUID.

Si una migración aún no aplicada falla por un tipo incorrecto, corrige el modelo y el archivo pendiente antes de reintentar. Cambiar solo el modelo no reescribe una migración existente. Conserva la revisión vacía ya aplicada; las modificaciones futuras se registran en nuevas migraciones.

Si no aparece `Running upgrade ...`, consulta `current`, `heads` y `history`: puede no haber revisiones pendientes. Un `alembic check` correcto tampoco prueba que todos los modelos estén importados. Si aparece `Target database is not up to date`, revisa y aplica las migraciones pendientes antes de generar otra.

## Consultar PostgreSQL

El servicio se llama **`postgres`**, no `db`. Desde la terminal puedes entrar usando los valores configurados en `.env`; con los valores por defecto del Compose:

```powershell
docker compose exec postgres psql -U postgres -d joblist
```

Dentro de `psql`:

```sql
\conninfo
\l
\dt public.*
\d public.skills
\d public.user_skills
\d public.job_skills

SELECT * FROM public.skills LIMIT 20;
SELECT version_num FROM alembic_version;

\q
```

Usa `\c nombre_base` para cambiar de base. Las migraciones crean estructura; no cargan registros salvo que el archivo incluya inserciones.

Para DBeaver o pgAdmin desde Windows: host `localhost`, puerto `5433`, base y credenciales de `.env`. Desde los contenedores se usa `postgres:5432`. Si no ves las tablas, verifica la base seleccionada y actualiza la lista en tu cliente.

## Archivos que se conservan

| Ruta | Uso |
| --- | --- |
| `app/` | Código de la API y modelos en desarrollo |
| `migrations/`, `alembic.ini` | Historial y configuración del esquema |
| `test/`, `pytest.ini` | Pruebas automatizadas |
| `requirements.txt`, `requirements-dev.txt` | Dependencias de ejecución y pruebas |
| `Dockerfile`, `docker-compose.yml`, `scripts/entrypoint.sh` | Arranque con Docker |
| `docker-compose.prod.yml`, `nginx/` | Configuración de producción pendiente de completar |
| `scripts/security_probes.py` | Diagnósticos históricos de seguridad; algunas pruebas esperan comportamientos vulnerables |

Se conservaron los archivos privados `.env` y `.env.production`, los entornos locales y `joblist_backup.dump` porque contienen configuración, dependencias o datos. El respaldo ya estaba versionado: ignorar `*.dump` no lo elimina del historial. `.gitignore` evita nuevos logs y cachés; `.dockerignore` excluye configuración privada, entornos, cachés y respaldos de las próximas imágenes.

## Pendientes de seguridad y producción

El informe histórico se resumió aquí y sus pruebas se conservaron en `scripts/security_probes.py`. Sus hallazgos no se consideran corregidos: revisar unicidad y consumo atómico de refresh tokens, claims JWT obligatorios, revocación al cambiar credenciales, acceso a perfiles ajenos y confianza en proxies. También quedan validación uniforme de contraseñas y UUID, CORS para PATCH, cabeceras en errores, redacción de credenciales en logs, cobertura de rate limiting y controles de calidad.

La auditoría anterior señaló una credencial en el historial Git: eliminar documentos no la rota ni borra el historial. Producción necesita variables coherentes para API/PostgreSQL, dominio y certificados reales; su health check todavía apunta a `/health/liveness`, una ruta inexistente. No se verificó un despliegue de producción ni se repitió la auditoría de dependencias en esta limpieza.
