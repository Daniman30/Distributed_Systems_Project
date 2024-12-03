FROM nginx:latest

# Instalar ping
RUN apt-get update && apt-get install -y inetutils-ping

# Copiar la configuración de Nginx
COPY nginx.conf /etc/nginx/nginx.conf

# Exponer el puerto 80
EXPOSE 80

