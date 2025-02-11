# Dependencias
import hashlib
import socket

# Hashear la data
def set_id(data: str) -> int:
    """
    Hashea una cadena usando SHA-1 y devuelve un entero.
    """
    return int(hashlib.sha1(data.encode()).hexdigest(), 16) % (2 ** 160)

# Obtener mi IP
def get_ip() -> str:
    """
    Obtiene la dirección IP local.
    """
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
        try:
            # Usamos una IP arbitraria que no se encuentra en nuestra red
            s.connect(('10.254.254.254', 1))
            ip_local = s.getsockname()[0]
        except Exception:
            ip_local = '127.0.0.1'  # Fallback a localhost
        return str(ip_local)