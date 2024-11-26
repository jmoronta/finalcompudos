# Usar una imagen base de Python
FROM python:3.10-slim

# Configurar el directorio de trabajo
WORKDIR /app

# Instalar dependencias del sistema necesarias para OpenCV y MySQL client
RUN apt-get update && apt-get install -y \
    libgl1-mesa-glx \
    libglib2.0-0 \
    default-libmysqlclient-dev \
    && rm -rf /var/lib/apt/lists/*

# Copiar los archivos de tu aplicación al contenedor
COPY . /app

# Instalar las dependencias de Python
RUN pip install --no-cache-dir -r requirements.txt

# Copiar los certificados SSL (si los tienes)
COPY cert.pem /certs/
COPY key.pem /certs/

# Exponer el puerto en el que la aplicación escuchará
EXPOSE 8000

# Comando para iniciar la aplicación
CMD ["python3", "servidor.py", "-p", "8000"]

