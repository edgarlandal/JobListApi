# Auditoría de seguridad — JobList API

Fecha: 10 de septiembre de 2026. **Resultado: no aprobar el despliegue de producción en el estado auditado.**

Se revisaron los 24 controles solicitados: código, configuración, Docker/Nginx, requisitos Python, fixtures y pruebas. Se añadieron pruebas de diagnóstico aisladas y evidencias en `audit/`. No se modificó la lógica de la aplicación ni se rotaron secretos.

## Alcance y resultados ejecutados

| Comprobación | Resultado |
| --- | --- |
| Suite existente | 20 tests pasan |
| Pruebas de diagnóstico de esta auditoría | 14 pasan: confirman comportamientos actuales, incluidos fallos; **no significan que el sistema sea seguro** |
| pip-audit 2.10.1 sobre requirements.txt | 68 dependencias resueltas, 0 vulnerabilidades conocidas, 0 paquetes omitidos |
| Ruff 0.16.6, reglas E4/E7/E9/F, configuración aislada | 32 observaciones: F811=1, F401=13, F841=2, E402=16 |
| mypy 2.3.1 con check-untyped-defs | 19 errores; incluye 6 diagnósticos de Settings que requieren configurar el plugin de Pydantic |
| Versiones directas frente a PyPI | Actualizaciones disponibles de Alembic, asyncpg y psycopg2-binary |
| Configuración y secretos | Inspección local con salida de indicadores, nunca valores de credenciales |

La prueba de dependencias resuelve el requirements actual; no representa necesariamente los paquetes de una imagen ya construida. No se escanearon paquetes del sistema operativo de las imágenes, ni se validaron certificados, DNS, firewall o un despliegue público. No se hicieron pruebas destructivas, ataques de carga ni escrituras en PostgreSQL real. La concurrencia de refresh se evaluó por revisión de código, sin una prueba de carrera sobre PostgreSQL. El historial de secretos se inspeccionó específicamente para `alembic.ini`; no constituye un escaneo exhaustivo de todos los objetos Git.

## Matriz de los 24 controles

| # | Control | Estado | Evidencia y acción |
| --- | --- | --- | --- |
| 1 | Password hashing seguro | Conforme con mejoras | Argon2id, salt administrada por PasswordHasher; verificación correcta y rechazo de contraseña errónea. Falta rehash al cambiar parámetros y evitar trabajo pesado síncrono en el event loop. |
| 2 | JWT correctamente firmado | Parcial | Algoritmo viene de configuración y se rechaza otra firma. No se exige presencia de exp/iat/sub; un JWT firmado sin exp se acepta. F05. |
| 3 | Access tokens de corta duración | Parcial | 60 minutos en configuración local/default. Producción declara 30, pero su configuración no inicia de forma autónoma. Propuesta de política: 10–15 minutos, ajustable según riesgo. F05/F07. |
| 4 | Refresh token rotation | Fallo alto | Sin jti: dos emisiones de la misma familia en el mismo segundo son idénticas. F02. |
| 5 | Revocación de tokens | Parcial | Logout revoca un refresh; access sigue válido. Cambio de contraseña no revoca sesiones. F07. |
| 6 | Detección de refresh token reuse | Parcial / alto | Se revoca la familia al observar used_at/revoked, pero la lectura y escritura no son atómicas. F02/F03. |
| 7 | RBAC | Fallo alto | user consulta otro perfil por ID, incluidos datos de admin; no hay comprobación de propietario. Edición/listado/borrado sí exigen admin. F04. |
| 8 | Validación de inputs | Parcial | Registro valida email y password; PATCH acepta password de un carácter. UUID inválido produce 500; faltan límites de longitud. F08. |
| 9 | SQL Injection | Sin indicios en alcance | Consultas ORM parametrizadas; SELECT 1 constante. Login con payload SQL devuelve rechazo. No equivale a prueba exhaustiva de todos los futuros repositorios. |
| 10 | CORS | Parcial | Orígenes explícitos, sin wildcard en archivos inspeccionados. PATCH falta en métodos; preflight permitido por origen devuelve 400. F09. |
| 11 | CSRF si corresponde | No aplica al mecanismo actual | Autenticación enviada explícitamente en Authorization y refresh en JSON, sin cookies de sesión automáticas. Si el frontend introduce cookies, reevaluar CSRF/Origin/SameSite. |
| 12 | Rate limiting | Fallo alto | Login limita a 5/min, pero X-Forwarded-For permite cambiar la clave; límite default no cubre rutas sin decorador. Redis no se inyecta en Compose local. F06. |
| 13 | Security headers | Parcial | nosniff, DENY y Referrer-Policy en respuestas ordinarias; faltan en error 500 no manejado. X-Request-ID sí permanece. HSTS de FastAPI no está activado. F09. |
| 14 | HTTPS | Pendiente de despliegue | Nginx define TLS 1.2/1.3, redirección y HSTS; dominio/certificados son plantilla. No se verificó TLS real. F10. |
| 15 | Secrets fuera del código | Fallo alto | .env excluidos de Git, pero contraseña DB vigente en historial Alembic; COPY incluye secretos al no existir .dockerignore. F01. |
| 16 | Errores sin información sensible | Parcial | Error HTTP 500 genérico confirmado; health readiness incorpora str(exc) al log. Arranque Alembic tiene logging propio. F11. |
| 17 | Logs sin secretos | Parcial | Tests de redacción y correlación pasan; contraseña dentro de URL PostgreSQL no se redacta. test.log está versionado. F11. |
| 18 | Dependencias actualizadas | Parcial | 0 vulnerabilidades conocidas en resolución auditada; 3 dependencias directas no están en la última versión y hay rangos sin lock. F12. |
| 19 | PostgreSQL no expuesto innecesariamente | Parcial | Compose local publica 5433 en todas las interfaces y Redis 6379; archivo prod independiente no publica bases. F10. |
| 20 | Docker seguro | Parcial / alto | Multietapa y appuser no-root; sin .dockerignore, filesystem escribible, imágenes por tag y sin restricciones adicionales de capacidades. F01/F10. |
| 21 | Health checks | Fallo de despliegue | /health/liveness del Compose prod devuelve 404; rutas correctas bajo /api/v1. readiness solo valida SELECT 1, no esquema/Redis. F10. |
| 22 | Tests | Parcial | 20 pasan; archivos unit/test_security.py y unit/test_validations.py vacíos. Faltan regresiones de carrera, rotación real PostgreSQL, RBAC exhaustivo y despliegue. F13. |
| 23 | Linting | No pasa | 32 observaciones del baseline explícito, incluida función get_auth_service duplicada. F13. |
| 24 | Type checking | No pasa | 19 diagnósticos; distinguir tipos reales, integración de frameworks y plugin faltante. F13. |

## Hallazgos priorizados

### F01 — Alta: secretos en historial e imagen

**Evidencia:** `Dockerfile` usa `COPY . .` y `COPY . /app`; no existe `.dockerignore`. Ambos archivos de entorno existen en el contexto. Aunque `.gitignore` los excluye de Git, no los excluye de Docker. En el historial de `alembic.ini` aparece un valor que coincide con `DB_PASSWORD` actual. No se imprime ese valor. No se encontró coincidencia de los valores actuales buscados en el contenido actual de archivos versionados.

**Impacto:** quien obtenga el historial o una imagen con ese contexto puede recuperar credenciales. No se ha verificado acceso externo efectivo ni se afirma exposición pública del repositorio.

**Corrección:** rotar la contraseña afectada coordinando aplicación y PostgreSQL; excluir `.env*`, `.git`, entornos Python y logs del contexto; inyectar secretos al ejecutar. Evaluar imágenes e historial distribuidos. Borrar solo la línea actual no elimina versiones anteriores. La exclusión del contexto es una función específica de [.dockerignore](https://docs.docker.com/build/concepts/context/#dockerignore-files).

### F02 — Alta: refresh tokens idénticos y filas ambiguas

**Evidencia:** `app/core/security.py:create_jwt_token` usa sub, family_id y fechas; carece de jti aleatorio. Con tiempo fijo, dos llamadas producen el mismo JWT (prueba incluida). `AuthService.refresh_access_token` mantiene la familia; `RefreshToken.token_hash` no es único.

**Impacto:** login seguido de refresh dentro del mismo segundo puede devolver el token ya revocado e insertar el mismo hash otra vez. La consulta `scalar_one_or_none()` puede entonces fallar por múltiples filas. La rotación no garantiza un nuevo secreto.

**Corrección:** jti criptográficamente aleatorio por emisión, unicidad de token_hash y prueba de login→refresh inmediato→refresh siguiente. La protección mediante rotación está descrita en [OWASP OAuth2](https://cheatsheetseries.owasp.org/cheatsheets/OAuth2_Cheat_Sheet.html).

### F03 — Alta: consumo de refresh no atómico

**Evidencia estática:** `get_by_hash`, comprobación de revoked/used_at, `mark_as_used` y `create` son operaciones separadas; los repositorios hacen commits intermedios. No hay bloqueo de fila ni UPDATE condicional de token aún disponible.

**Impacto inferido:** dos solicitudes concurrentes pueden leer el mismo estado y crear descendientes válidos; una revocación de familia puede competir con la inserción de un descendiente. No se ha reproducido esta carrera en PostgreSQL.

**Corrección:** consumir y rotar dentro de una transacción, con bloqueo o UPDATE condicional y control de resultado, además de coordinar la revocación de familia. Añadir prueba concurrente con dos sesiones reales y asegurar que solo una rotación gana.

### F04 — Alta: acceso a perfiles ajenos

**Evidencia:** `app/api/routes/users.py:get_user_by_id` exige rol user, pero no comprueba `current_user.id == id`. La prueba con un token user obtiene 200 y el email del administrador creado por otro fixture. El UUID no constituye autorización. El esquema de respuesta también contiene nombres, rol y estado de cuenta.

**Corrección:** permitir perfil propio o administrador según política explícita; restringir campos si existe un directorio público intencional. Añadir pruebas de propietario, otro usuario, admin e inactivo en cada operación. Actualmente admin tampoco puede consultar por ID, aunque sí puede listar.

### F05 — Media: claims opcionales y duración JWT

**Evidencia:** `decode_acces_token` verifica firma y tipo, pero no utiliza `options={"require": [...]}`. La prueba acepta un token correctamente firmado sin exp. Esto requiere un token emitido/firmado por una fuente con acceso a la clave; no es un bypass de firma por un atacante sin clave.

**Corrección:** exigir exp, iat, sub y type; usar identidad UUID estable en sub y definir issuer/audience si corresponde a los consumidores. Evaluar 10–15 minutos de access como política del proyecto y validar valores positivos/máximos de TTL. La mera validación de expiración no obliga a que exista el claim: [PyJWT API](https://pyjwt.readthedocs.io/en/stable/api.html).

### F06 — Alta: límites eludibles y cobertura incompleta

**Evidencia:** tras cinco logins fallidos, el sexto devuelve 429; con un X-Forwarded-For nuevo vuelve a 400, es decir, ejecuta el login. `app/main.py` confía en proxies `*`. También 101 solicitudes a health devuelven 200 pese a default_limits=100/minute. `SlowAPIMiddleware` no se instala. `docker-compose.yml` no exporta REDIS_URL; SlowAPI lee os.getenv y cae en memoria, separada entre cuatro workers.

**Corrección:** confiar solo en proxies controlados y configurar cómo reemplazan cabeceras de origen; combinar límites por cuenta/IP para login y proteger los endpoints costosos. Instalar/configurar cobertura global si se desea y excluir health explícitamente. Inyectar Redis compartido y decidir el comportamiento ante su caída. La prueba de spoofing usa ASGI directo: el alcance externo depende de si un proxy confiable sanea las cabeceras y de si la API es accesible directamente.

### F07 — Media: revocación incompleta de sesiones

**Evidencia:** logout revoca el refresh, pero el access anterior sigue accediendo a /users/me (200 confirmado). Actualizar contraseña no invalida refresh/access; la revocación de familia no revoca access tokens. El mensaje «All sessions revoked» sobre reuse es más amplio que la acción real sobre una familia.

**Corrección:** definir la semántica de logout y cierre global. Usar access corto y, si se requiere revocación inmediata, versión de sesión/usuario o denylist. Invalidar sesiones al cambiar credenciales; conservar bloqueo por is_active, que ya se consulta en cada petición.

### F08 — Media: validación desigual y consumo de recursos

**Evidencia:** `UserUpdate(..., password="x")` es válido, mientras UserCreate exige política. UUID inválido llega a `UUID(user_id)` y produce 500. Campos de texto no tienen máximos acordes con columnas de 255. Argon2 se ejecuta síncronamente dentro de handlers async, susceptible a bloqueo del event loop bajo trabajo costoso. `POST /users` es público, sin decorador de límite y su servicio omite firstname/lastname al crear el modelo.

**Corrección:** validadores compartidos, UUID en parámetros FastAPI, límites de longitud y tamaño de cuerpo aplicables también cuando se accede directo a API. Ejecutar hashing fuera del event loop y medir límites de concurrencia. Consolidar el registro en un único servicio protegido. Los parámetros actuales de Argon2id son una base apropiada; [OWASP Password Storage](https://cheatsheetseries.owasp.org/cheatsheets/Password_Storage_Cheat_Sheet.html) recomienda esta familia de algoritmos.

### F09 — Media: CORS y cabeceras en respuestas de error

**Evidencia:** preflight PATCH desde un origen permitido devuelve 400 porque falta PATCH. En un error no manejado de UUID, la respuesta 500 conserva X-Request-ID y cuerpo genérico pero no X-Frame-Options: el wrapper de errores está fuera de SecurityHeadersMiddleware. El HSTS condicional de FastAPI no se activa desde settings; su cadena contiene además `reload`.

**Corrección:** permitir PATCH cuando corresponde, asegurar CORS/cabeceras también en errores y administrar HSTS en el proxy HTTPS efectivo. No activar HSTS en desarrollo HTTP ni interpretar la ausencia de CSP en una API JSON como un bypass de autenticación; revisar CSP por separado para páginas HTML como Swagger.

### F10 — Alta para operatividad / media para endurecimiento: producción no preparada

**Evidencia:** `.env.production` no define ninguna de las seis claves obligatorias `DB_HOST`, `DB_PORT`, `DB_NAME`, `DB_USER`, `DB_PASSWORD`, `JWT_SECRET_KEY`. No es simplemente una clave JWT corta: está ausente con el nombre esperado. Puede heredar accidentalmente `.env` copiado en imagen, pero no constituye configuración autónoma de producción. El health check apunta a una ruta 404. Nginx contiene `tudominio.com` y rutas de certificados de ejemplo; Compose no contiene emisión/renovación automática. No se ejecutó ese despliegue durante la auditoría.

Compose local publica PostgreSQL y Redis en todas las interfaces; producción independiente no los publica. El usuario DB local predeterminado es postgres. Docker sí utiliza appuser no-root, pero no configura filesystem de solo lectura, no-new-privileges o cap_drop, y las imágenes no están fijadas por digest. No existen revisiones fuente en migrations/versions: readiness puede dar 200 sin tablas.

**Corrección:** definir DB_* y JWT_SECRET_KEY de producción y comprobar coherencia con POSTGRES_*; excluir fallback de desarrollo del artefacto. Corregir health a /api/v1/health/ready; verificar dominio, certificados y renovación. Limitar puertos locales a loopback cuando no se requiera acceso remoto. Separar usuario de migración y usuario runtime con privilegios mínimos. Versionar esquema y endurecer la imagen conforme a lo que necesite escribir.

### F11 — Media: redacción parcial de logs

**Evidencia:** el logger estructurado omite tracebacks y redacta claves y JWT, y sus tests pasan. Sin embargo, `redact_sensitive_data` conserva la contraseña sintética en `postgresql://audit:...@db/test`. `healthy.py` interpola str(exc) en un mensaje. La combinación puede filtrar credenciales si un error incluye una URL; no se afirma haber encontrado una credencial real en los logs actuales. Alembic/entrypoint no se inicializa con setup_logging de app.main. `test.log` está versionado.

**Corrección:** eventos constantes y exception_type en health y arranque, redacción de URIs como defensa adicional, excluir logs de Git e imagen y probar errores de drivers con secretos sintéticos. Mantener las respuestas HTTP genéricas ya existentes.

### F12 — Baja: reproducibilidad y actualización de dependencias

pip-audit consultó PyPI y no detectó vulnerabilidades conocidas en los 68 paquetes resueltos, sin omitidos. Esto no garantiza ausencia de vulnerabilidades desconocidas, de lógica o del sistema operativo.

| Dependencia | Fijada | Última consultada en PyPI |
| --- | --- | --- |
| Alembic | 1.19.1 | 1.19.2 |
| asyncpg | 0.29.0 | 0.31.0 |
| psycopg2-binary | 2.9.12 | 2.9.13 |

Fuentes de versión: [Alembic](https://pypi.org/pypi/alembic/json), [asyncpg](https://pypi.org/pypi/asyncpg/json), [psycopg2-binary](https://pypi.org/pypi/psycopg2-binary/json). No se atribuye un CVE a estos desfases. Uvicorn, Redis y SlowAPI tienen especificaciones abiertas; falta lock con hashes. Revisar también la necesidad del paquete `argon2` además de `argon2-cffi`, y mover herramientas de auditoría fuera del runtime si no son necesarias.

### F13 — Media para calidad: faltan gates de tests y análisis estático

Los 20 tests de aplicación pasan, pero no cubren la rotación exitosa completa con fechas PostgreSQL ni carreras de revocación. Las pruebas de auditoría demuestran comportamientos inseguros mediante aserciones de observación; después de corregirlos hay que invertir expectativas y convertirlos en regresiones de seguridad.

Ruff identifica 32 problemas: no todos son vulnerabilidades; E402 incluye orden intencional de inicialización de logs y fixtures. Mypy identifica 19: seis avisos de Settings requieren plugin/configuración, mientras que `__init__ -> User | None`, tipos opcionales incompatibles y `get_auth_service` duplicada merecen corrección real. No se han ocultado mediante auto-fixes ni ignores masivos.

## Reproducción y archivos de evidencia

Las herramientas se instalaron en `.venv` para la auditoría, sin modificar requirements de la aplicación. Desde la raíz:

```powershell
.venv/Scripts/python.exe -m pip install ruff==0.16.6 mypy==2.3.1 pip-audit==2.10.1
.venv/Scripts/python.exe -m pytest -q -p no:cacheprovider
.venv/Scripts/python.exe -m pytest audit/security_probes.py -q -p no:cacheprovider
.venv/Scripts/python.exe -m ruff check app migrations test --isolated --no-cache --select E4,E7,E9,F
.venv/Scripts/python.exe -m mypy app --explicit-package-bases --ignore-missing-imports --check-untyped-defs --cache-dir audit/.mypy_cache
.venv/Scripts/python.exe -m pip_audit -r requirements.txt --format json --progress-spinner off
```

- [Pruebas de diagnóstico](audit/security_probes.py) y [resultado](audit/probes.txt).
- [Dependencias auditadas](audit/dependencies.json) y [versiones comparadas](audit/dependency_versions.json).
- [Ruff](audit/ruff.json) y [mypy](audit/mypy.txt).
- [Indicadores de configuración sin secretos](audit/config_checks.json).

Las pruebas usan SQLite en memoria y valores ficticios; no ejecutan migraciones ni atacan el servidor real. Ruff utiliza un baseline explícito sin heredar configuración externa. Mypy omite imports sin stubs, por lo que su cobertura es parcial. El análisis de dependencias requirió acceso al índice y creación de caché fuera del sandbox; terminó correctamente.

## Orden recomendado de cierre

1. Rotar la credencial expuesta y evitar inclusión de secretos en imágenes (F01).
2. Corregir unicidad/transacciones de refresh, autorización por objeto y confianza de proxy (F02–F06).
3. Completar configuración de producción, esquema, HTTPS y checks (F10).
4. Homogeneizar validación, revocación, logs y cabeceras (F07–F09/F11).
5. Añadir regresiones PostgreSQL y gates de CI para tests, lint, tipos y dependencias (F12/F13).

No se marca ninguno de estos hallazgos como corregido por haber generado el informe.
