# Imagen base ligera y oficial de Python
FROM python:3.12-slim

# Evita .pyc y fuerza logs sin buffer (utiles en `docker logs`)
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    STREAMLIT_SERVER_PORT=8501 \
    STREAMLIT_SERVER_ADDRESS=0.0.0.0

WORKDIR /app

# curl se usa solo para el HEALTHCHECK del contenedor
RUN apt-get update \
    && apt-get install -y --no-install-recommends curl \
    && rm -rf /var/lib/apt/lists/*

# Dependencias primero: aprovecha la cache de capas de Docker
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Codigo de la aplicacion y dataset
COPY .streamlit/ ./.streamlit/
COPY data/ ./data/
COPY app.py .

# Usuario sin privilegios (buena practica de seguridad)
RUN useradd --create-home appuser && chown -R appuser:appuser /app
USER appuser

EXPOSE 8501

HEALTHCHECK --interval=30s --timeout=5s --start-period=20s --retries=3 \
    CMD curl -fsS http://localhost:8501/_stcore/health || exit 1

ENTRYPOINT ["streamlit", "run", "app.py", "--server.port=8501", "--server.address=0.0.0.0"]
