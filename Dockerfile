# Usar una imagen base de Python
FROM python:3.10-slim

# Configurar el directorio de trabajo
WORKDIR /

# Instala dependencias del sistema necesarias para OpenCV
RUN apt-get update && apt-get install -y \
    libgl1-mesa-glx \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*
    	
# Copia los archivos de tu aplicación al contenedor
COPY . /app
# Copiar los archivos de requisitos y el código fuente
COPY requirements.txt requirements.txt
COPY . .

# Copia los certificados SSL al contenedor
COPY cert.pem /certs/
COPY key.pem /certs/

# Copia el script SQL al contenedor
COPY init.sql /docker-entrypoint-initdb.d/

# Cambia los permisos para el archivo (opcional)
RUN chmod 755 /docker-entrypoint-initdb.d/init.sql



# Instalar las dependencias
RUN pip install --no-cache-dir -r requirements.txt

# Copiar el resto del código fuente de la aplicación
COPY . .

# Exponer el puerto en el que la aplicación escuchará
EXPOSE 8000

# Comando para iniciar la aplicación
CMD ["python3", "servidor.py","-p 8000"]

