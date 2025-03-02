import hashlib
import socket
import threading
import random
import time
import queue
TCP_PORT = 8000  # puerto de escucha del socket TCP
UDP_PORT = 8888  # puerto de escucha del socket UDP
# Definición de operaciones Chord
JOIN = 'join'
CONFIRM_JOIN = 'conf_join'
FIX_FINGER = 'fix_fing'
FIND_FIRST = 'fnd_first'
REQUEST_DATA = 'req_data'
CHECK_PREDECESSOR = 'check_pred'
NOTIFY = 'notf'
UPDATE_PREDECESSOR = 'upt_pred'
UPDATE_FINGER = 'upd_fin'
UPDATE_SUCC = 'upd_suc'
DATA_PRED = 'dat_prd'
FALL_SUCC = 'fal_suc'

REGISTER = 'reg'
LOGIN = 'log'
ADD_CONTACT = 'add_cnt'
LIST_PERSONAL_AGENDA = 'list_personal_agenda'
LIST_GROUP_AGENDA = 'list_group_agenda'
CREATE_GROUP = 'create_group'
DELETE_GROUP = 'delete_group'
LEAVE_GROUP = 'leave_group'
ADD_MEMBER = 'add_member'
REMOVE_MEMBER = 'remove_member'
LIST_GROUPS = 'list_groups'
CREATE_EVENT = 'create_event'
CREATE_GROUP_EVENT = 'create_group_event'
CREATE_INDIVIDUAL_EVENT ='create_individual_event'
CONFIRM_EVENT = 'confirm_event'
CANCEL_EVENT = 'cancel_event'
LIST_EVENTS = 'list_events'
LIST_EVENTS_PENDING = 'list_events_pending'
LIST_CONTACTS = 'list_contacts'
REMOVE_CONTACT = 'remove_contact'
LIST_MEMBER = 'list_member'
BROADCAST_IP = '255.255.255.255'

class ChordNode:
    def __init__(self):
        self.ip = self.get_ip()
        self.id = self.generate_id()
        self.port = TCP_PORT
        self.predecessor = NodeReference(self.ip, self.port)
        self.succesor = NodeReference(self.ip, self.port)
        self.ip_table = {} # IPs table: {ID: {IP, port}}
        self.finger_table = self.create_finger_table() # Finger table: {ID: Owner}
        # self.db = Database()

        threading.Thread(target=self.start_tcp_server).start()
        threading.Thread(target=self.handle_finger_table).start()

        self.join()

    def start_tcp_server(self):
        """Iniciar el servidor TCP."""
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            s.bind((self.ip, self.port))
            print(f'Socket TCP binded to ({self.ip}, {self.port})')
            s.listen()

            # Se queda escuchando cualquier mensaje entrante
            while True:
                time.sleep(1)
                conn, addr = s.accept()
                client = threading.Thread(target=self._handle_client_tcp, args=(conn, addr))
                client.start()

    def _handle_client_tcp(self, conn: socket.socket, addr: tuple):
        # Maneja el mensaje entrante
        data = conn.recv(1024).decode().split('|') # operation | id | port
        option = data[0]
        if option == '':
            return
        id = data[1]
        port = data[2]

        if option == JOIN:
            # No hacer nada si recibo la operacion de mi mismo
            if self.id == id:
                pass
            # Me estoy uniendo a una red donde solo hay un nodo
            elif self.id == self.succesor.id:
                # Actualiza mi self.succesor a id
                op = UPDATE_SUCC
                data = f'{self.succesor.id}|{self.succesor.port}|{id}|{port}'
                self.send_data(op, data)
                
                # Actualiza mi self.predecessor a id
                op = UPDATE_PREDECESSOR
                data = f'{self.predecessor.id}|{self.predecessor.port}|{id}|{port}'
                self.send_data(op, data)

                # Actualiza id.sucesor a self.id
                op = UPDATE_SUCC
                data = f'{id}|{port}|{self.id}|{self.port}'
                self.send_data(op, data)
                # Actualiza id.predecesor a self.id
                op = UPDATE_PREDECESSOR
                data = f'{id}|{port}|{self.id}|{self.port}'
                self.send_data(op, data)
            # Hay 2 nodos o mas
            # Esta entre yo y mi predecesor
            elif self.id < id and self.predecessor.id > id:
                # Actualiza mi self.succesor a id
                op = UPDATE_SUCC
                data = f'{self.succesor.id}|{self.succesor.port}|{id}|{port}'
                self.send_data(op, data)
                
                # Actualiza mi self.predecessor a id
                op = UPDATE_PREDECESSOR
                data = f'{self.predecessor.id}|{self.predecessor.port}|{id}|{port}'
                self.send_data(op, data)

                # Actualiza id.sucesor a self.id
                op = UPDATE_SUCC
                data = f'{id}|{port}|{self.id}|{self.port}'
                self.send_data(op, data)
                # Actualiza id.predecesor a self.id
                op = UPDATE_PREDECESSOR
                data = f'{id}|{port}|{self.id}|{self.port}'
                self.send_data(op, data)


        print("conn, addr, data", conn, addr, data)
        print("option, info, ip, port", option, id, port)

    def send_data(self, op, data):
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:  # 🔹 Cambiar a TCP (SOCK_STREAM)
                s.connect((self.ip, self.port))  # 🔹 Conectar al servidor TCP
                s.sendall(f'{op}|{data}'.encode('utf-8'))  # 🔹 Enviar mensaje correctamente
                print(f"Mensaje enviado correctamente vía TCP. Operation: {op} Data: {data}")
        except Exception as e:
            print(f"Mensaje fallido. Operation: {op} Data: {data} Error: {e}")

    def join(self):
        op = JOIN
        data = f'{self.id}|{self.port}'
        self.send_data(op, data)

    def create_finger_table(self):
        table = {}
        id = self.id
        for i in range(8):
            self.ip_table[id] = self.ip
            table[(id + 2**i) % 256] = id
        return table

    def handle_finger_table(self):
        while True:
            time.sleep(1)
            for id, owner in self.finger_table.items():
                ip = self.id_to_ip(owner)
                if not self.verificar_ip_activa(ip, TCP_PORT):
                    self.fix_finger_table()
                    break

    def fix_finger_table(self):
        """
        Corrige la tabla de fingers si un nodo deja de responder o cambia la red.
        """
        print("[!] Verificando y corrigiendo tabla de fingers...")
        for i in range(8):
            finger_id = (self.id + 2**i) % 256
            new_node = self.find_successor(finger_id)
            if new_node:
                self.finger_table[finger_id] = new_node
                print(f"[+] Finger {finger_id} actualizado a {new_node}")
    
    def find_successor(self, k):
        """
        Encuentra el sucesor de un nodo dado en la red Chord.
        """
        sorted_ids = sorted(self.finger_table.keys())
        for node_id in sorted_ids:
            node = self.finger_table[node_id]
            if node_id >= k and self.verificar_ip_activa(node, TCP_PORT):
                return node
        return self.succesor if self.verificar_ip_activa(self.succesor, TCP_PORT) else self.id

    def verificar_ip_activa(self, ip, puerto):
        """
        Verifica si una IP está activa en un puerto TCP específico.

        :param ip: Dirección IP a verificar (str).
        :param puerto: Puerto TCP a verificar (int).
        :return: True si la IP está activa en el puerto, False en caso contrario.
        """
        # Crear un socket TCP
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(3)  # Tiempo de espera máximo en segundos

        try:
            # Intentar conectar al puerto
            resultado = sock.connect_ex((ip, puerto))
            if resultado == 0:
                print(f"[+] La IP {ip} está activa en el puerto {puerto}.")
                return True
            else:
                print(f"[-] La IP {ip} no responde en el puerto {puerto}. Código de error: {resultado}")
                return False
        except Exception as e:
            print(f"[!] Error al conectar con {ip}:{puerto}. Detalles: {e}")
            return False
        finally:
            # Cerrar el socket
            sock.close()

    def get_ip(self) -> str:
        """
        Obtiene la dirección IP local.
        """
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
            try:
                # Usamos una IP arbitraria que no se encuentra en nuestra red
                s.connect(('8.8.8.8', 80))
                ip_local = s.getsockname()[0]
                # ip_local = f'127.198.1.1{random.randint(10, 99)}'
                print("ip_local", ip_local)
            except Exception:
                ip_local = f'10.2.0.{random.randint(2, 10)}'  # Fallback a localhost
            return str(ip_local)
        
    def id_to_ip(self, id):
        return self.ip_table[id]

    def generate_id(self):
        """Genera un ID único basado en el hash de la IP y puerto."""
        # Obtener mi IP
        node_info = f"{self.ip}"
        return int(hashlib.sha1(node_info.encode()).hexdigest(), 16) % (2 ** 8)


class NodeReference:
    def __init__(self, ip: str, port: int):
        self.id = self.set_id(ip)
        self.ip = ip
        self.port = port
    
    # Hashear la data
    def set_id(self, data: str) -> int:
        """
        Hashea una cadena usando SHA-1 y devuelve un entero.
        """
        return int(hashlib.sha1(data.encode()).hexdigest(), 16) % (2 ** 8)

if __name__ == "__main__":

    server = ChordNode()