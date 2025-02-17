# Usa Python 3.10 como base
FROM python:3.10

# Instalar herramientas básicas
RUN apt-get update && apt-get install -y inetutils-ping

# Configurar el directorio de trabajo
WORKDIR /app

# Copiar el archivo de dependencias
COPY requirements.txt /app/

# Instalar las dependencias necesarias
RUN pip install --no-cache-dir -r requirements.txt

# Copiar el resto del código al contenedor
COPY chord_dht/ /app/chord_dht/

# Exponer los puertos para Flask y Chord
EXPOSE 5000 8000 8880

# Variables de entorno
ENV NODE_IP="0.0.0.0"
ENV NODE_PORT_TCP=8000
ENV NODE_PORT_UDP=8880

# Ejecutar Flask y Chord al iniciar el contenedor
# CMD ["sh", "-c", "python chord_dht/chord.py & chord_dht/python app.py"]
# CMD ["sh", "-c", "python chord_dht/chord.py & python chord_dht/python app.py"]
CMD ["sh", "-c", "python chord_dht/chord.py & python chord_dht/app.py"]
