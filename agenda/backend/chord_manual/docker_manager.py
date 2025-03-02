import subprocess

NETWORK_NAME = "chord_network"
BASE_IP = "172.18.0."
BASE_PORT_TCP = 8000
BASE_PORT_UDP = 8880
MAX_NODES = 10

def get_active_nodes():
    """Obtiene una lista de nodos activos en la red."""
    command = ["docker", "ps", "--format", "{{.Names}}"]
    result = subprocess.run(command, capture_output=True, text=True)
    return result.stdout.splitlines()

def get_next_available_ip():
    """Encuentra la siguiente IP disponible para un nodo."""
    used_ips = [BASE_IP + "2", BASE_IP + "3"]  # Reservadas para backend y frontend
    nodes = get_active_nodes()
    num = len(nodes) + len(used_ips)

    return f"{BASE_IP}{num + 2}"

def get_next_available_ports():
    """Encuentra los siguientes puertos disponibles para un nodo."""
    nodes = get_active_nodes()
    return BASE_PORT_TCP + len(nodes), BASE_PORT_UDP + len(nodes)

def check_network_exists(network_name):
    """Verifica si la red Docker ya existe."""
    command = ["docker", "network", "inspect", network_name]
    try:
        subprocess.run(command, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        return True  # La red existe
    except subprocess.CalledProcessError:
        return False  # La red no existe

def create_network():
    """Crea una nueva red Docker si no existe."""
    network_name = "chord_network"
    subnet = "172.20.0.0/16"
    driver = "bridge"

    if check_network_exists(network_name):
        print(f"La red '{network_name}' ya existe. No se realizará ninguna acción.")
        return

    command = [
        "docker", "network", "create",
        "--driver", driver,
        "--subnet", subnet,
        network_name
    ]

    try:
        subprocess.run(command, check=True)
        print(f"Red '{network_name}' creada con éxito.")
    except subprocess.CalledProcessError as e:
        print(f"Error al crear la red: {e}")

def create_node():
    """Crea un nuevo nodo."""
    if len(get_active_nodes()) >= MAX_NODES:
        print("Máximo número de nodos alcanzado.")
        return

    node_name = input("Ingrese el nombre del nodo: ")
    node_ip = get_next_available_ip()
    node_port_tcp, node_port_udp = get_next_available_ports()

    if not node_ip:
        print("No hay IPs disponibles.")
        return

    command = [
        "docker", "run", "-d",
        "--name", node_name,
        "--network", NETWORK_NAME,
        "--ip", node_ip,
        "-e", f"NODE_IP={node_ip}",
        "-e", f"NODE_PORT_TCP={node_port_tcp}",
        "chord"
    ]

    try:
        subprocess.run(command, check=True)
        print(f"Nodo '{node_name}' creado con IP {node_ip}.")
    except subprocess.CalledProcessError as e:
        print(f"Error al crear el nodo: {e}")

def delete_node():
    """Elimina un nodo existente."""
    node_name = input("Ingrese el nombre del nodo a eliminar: ")
    
    command = ["docker", "rm", "-f", node_name]
    try:
        subprocess.run(command, check=True)
        print(f"Nodo '{node_name}' eliminado.")
    except subprocess.CalledProcessError as e:
        print(f"Error al eliminar el nodo: {e}")

def main():
    """Menú interactivo."""
    create_network()
    while True:
        print("\n1. Crear Nodo\n2. Eliminar Nodo\n3. Salir")
        choice = input("Seleccione una opción: ")

        if choice == "1":
            create_node()
        elif choice == "2":
            delete_node()
        elif choice == "3":
            print("Saliendo...")
            break
        else:
            print("Opción no válida.")

if __name__ == "__main__":
    main()
