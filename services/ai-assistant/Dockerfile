FROM python:3.12-slim

WORKDIR /app

# Build context is services/ so shared/ is accessible
COPY shared/ /app/shared/

# Install shared library dependencies first
RUN pip install --no-cache-dir -r /app/shared/requirements.txt

# Install service-specific dependencies
COPY ai-assistant/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY ai-assistant/app/ ./app/

EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
