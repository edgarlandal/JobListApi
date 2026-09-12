# Test API
.venv/Scripts/python.exe -m pytest -q -p no:cacheprovider

# Run API
docker compose build

docker compose up -d  

# Log API
docker compose logs -f api

# Migration
La API ejecuta `alembic upgrade head` al arrancar. Para aplicar las
migraciones del proyecto, incluyendo `jobs`:

```powershell
docker compose up -d --build api
docker compose exec api alembic current
docker compose exec api alembic check
```

Para crear futuras migraciones desde PowerShell, registra el modelo en
`app/models/__init__.py` y ejecuta desde la raiz del proyecto:

```powershell
docker compose build api
docker compose run --rm --no-deps --entrypoint alembic -v "${PWD}/migrations:/app/migrations" api upgrade head
docker compose run --rm --no-deps --entrypoint alembic -v "${PWD}/migrations:/app/migrations" api revision --autogenerate -m "your_message"
# Revisa el archivo generado antes de aplicarlo.
docker compose up -d --build api
```

El montaje guarda los archivos generados en tu proyecto. `exec` requiere
que la API este funcionando; `run --entrypoint alembic` sirve incluso si
esta reiniciandose por una migracion pendiente.

La revision `8a1609544292` es una base reconstruida del esquema existente
en Docker (users y refresh_token), no el historial original completo.
No borres `alembic_version` ni uses `stamp head` para omitir cambios.
El `.env` local puede apuntar a una base distinta: estos comandos usan
PostgreSQL de Docker.
