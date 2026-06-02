@echo off
echo Generating documentation...

echo [1/4] Generating shared library docs...
docker compose exec recruitment python -m pdoc /app/shared --output-dir /tmp/shared-docs --no-search
if %errorlevel% neq 0 (
    echo ERROR: Failed to generate shared docs. Is docker compose up?
    exit /b 1
)

echo [2/4] Generating recruitment service docs...
docker compose exec recruitment python -m pdoc /app --output-dir /tmp/docs --no-search
if %errorlevel% neq 0 (
    echo ERROR: Failed to generate recruitment docs.
    exit /b 1
)

echo [3/4] Copying docs out of container...
if not exist docs\generated\shared mkdir docs\generated\shared
if not exist docs\generated\recruitment mkdir docs\generated\recruitment
docker cp ubs-ttp-recruitment-1:/tmp/shared-docs/. docs/generated/shared
docker cp ubs-ttp-recruitment-1:/tmp/docs/. docs/generated/recruitment

echo [4/4] Done!
echo.
echo Open docs\generated\shared\index.html to view shared library docs.
echo Open docs\generated\recruitment\index.html to view recruitment service docs.
