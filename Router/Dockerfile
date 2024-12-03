FROM debian:latest

# Configurar el entorno
WORKDIR /app

# Exponer el puerto 80 para las solicitudes
EXPOSE 80

# Copiar el script del router al contenedor
COPY router.sh /app/router.sh

# Dar permisos de ejecución al script
RUN chmod +x /app/router.sh

# Ejecutar el router al iniciar el contenedor
CMD ["./router.sh"]
