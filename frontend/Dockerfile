# Imagen base de Python
FROM python:3.9-slim

# Establecer el directorio de trabajo
WORKDIR /app

# Copiar el archivo de requisitos
#COPY requirements.txt /app/

# Instalar dependencias
#RUN pip install --no-cache-dir -r requirements.txt

# Copiar el código del frontend
COPY . /app/

# Establecer las variables de entorno para Django
ENV PYTHONUNBUFFERED 1

# Exponer el puerto 8080 para servir el frontend
EXPOSE 8080

# Comando para ejecutar el servidor de Django para el frontend
#CMD ["python", "manage.py", "runserver", "0.0.0.0:8080"]


# Comando para iniciar un servidor HTTP básico
CMD ["python", "-m", "http.server", "8080"]

