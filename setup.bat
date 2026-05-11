@echo off
echo Setting up UBS TTP development environment...

echo [1/3] Copying .env.example to .env...
if not exist .env (
    copy .env.example .env
    echo .env created
) else (
    echo .env already exists, skipping
)

echo [2/3] Installing Python dev tools...
pip install -r requirements-dev.txt --user

echo [3/3] Installing frontend dependencies...
cd frontend && npm install && cd ..

echo.
echo Setup complete!
echo.
echo To start the app:   docker compose up --build
echo To run linting:     python -m ruff check services/
echo To run security:    python -m bandit -r services/ -ll -q
