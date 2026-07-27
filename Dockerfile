# Imagen base ligera de Python 3.11
FROM python:3.11-slim

# Evitar escritura de bytecode y habilitar buffer de salida
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PORT=8080

# Directorio de trabajo
WORKDIR /app

# Instalar dependencias del sistema necesarias
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copiar e instalar requerimientos
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copiar el código de la aplicación y datos de prueba
COPY . /app/

# Exponer el puerto configurado (GCP Cloud Run usa 8080 por defecto)
EXPOSE 8080

# Comando de arranque optimizado para GCP Cloud Run
CMD ["sh", "-c", "streamlit run app.py --server.port=${PORT} --server.address=0.0.0.0 --server.headless=true --server.enableCORS=false"]
