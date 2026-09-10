# Test API
.venv/Scripts/python.exe -m pytest -q -p no:cacheprovider

# Run API
docker compose build

docker compose up -d  

# Log API
docker compose logs -f api