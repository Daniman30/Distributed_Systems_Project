import hashlib
import socket
import threading
import random
import time
import queue
from backend.chord_dht.utils import get_ip,set_id
from backend.chord_dht.communication import ChordNode, BroadcastRef,send_data
from backend.chord_dht.communication import JOIN,CONFIRM_JOIN,FIX_FINGER,FIND_FIRST,REQUEST_DATA,CHECK_PREDECESSOR,NOTIFY,UPDATE_PREDECESSOR,UPDATE_FINGER,UPDATE_SUCC,DATA_PRED,FALL_SUCC
from backend.chord_dht.handle_data import HandleData
TCP_PORT = 8000 #puerto de escucha del socket TCP
UDP_PORT = 8888 #puerto de escucha del socket UDP

class ChordNode:
    def __init__(self, ip: str, port_tcp=8000,port_udp =8888):
        self.ip = get_ip() #ARREGLAR ESTO
        self.port_udp = port_udp
        self.port_tcp = port_tcp
        self.id = self._generate_id()
        self.reference= ChordNode(self.ip, self.port_tcp)
        self.predecessor = None
        self.successor = self.reference
        self.broadcast = BroadcastRef(self.port_udp)
        self.finger_table = [self.reference] * 160
        self.joined = False
        self.joined_confirmed= False
        self.handler_data = HandleData(self.id)
        self.leader:bool
        self.first:bool
        self.repli_pred=''
        self.grandpa_data = ''
        self.running = True
        self.fix_finger_queue = queue.Queue()
        self.update_finger_queue = queue.Queue()
        
        # Iniciar los servidores TCP y UDP
        threading.Thread(target=self.start_broadcast_server).start()
        threading.Thread(target=self.start_tcp_server).start()
        threading.Thread(target=self.start_udp_server).start()
        threading.Thread(target=self.set_leader).start()
        threading.Thread(target=self.check_first).start()
        threading.Thread(target=self.print_info).start()
        threading.Thread(target=self._check_predecessor).start()
        threading.Thread(target=self.handle_fix_finger).start()
        threading.Thread(target=self.handle_update_finger).start()
        
        while True:
            self.broadcast.join()
            time.sleep(5)
            if self.joined:
                break
          
        self.broadcast.fix_finger()
        if self.pred != None:
            pass
    def _generate_id(self):
        """Genera un ID único basado en el hash de la IP y puerto."""
        node_info = f"{self.ip}"
        return int(hashlib.sha1(node_info.encode()).hexdigest(), 16) % (2 ** 160)
    
    def _closest_preceding_node(self, id):
        """Devuelve el nodo más cercano a un ID en la finger table."""
        for i in range(160):
            if self.id + (2**i) > id:
                return self.finger_table[i-1]
 
    def fix_fingers(self, node:ChordNode, id = None):
        """Actualiza la tabla de fingers cuando entra un nodo."""
        for i in range(160): 
            if id != None:
                if self.finger_table[i].id == id:
                    self.finger_table[i] = node 
            else:
                if node.id < self.finger_table[i].id:
                #si el nodo entrante es menor que el nodo en cuestion y se puede hacer cargo de ese id, actualizamos
                    if self.id + (2 ** i) <= node.id:
                        self.finger_table[i] = node

                #si el nodo entrante es mayor, pero el nodo en cuestion esta manejando un dato de mayor id que el
                elif self.finger_table[i].id < self.id + 2 ** i:
                    self.finger_table[i] = node
         

    def handle_fix_finger(self):
        """Arregla la tabla de fingers periódicamente."""
        while True:
            ip, port = self.fix_finger_queue.get()
            try:
                ref = ChordNode(ip, port)
                self.fix_fingers(ref)
                print('Finger table fixed!')
            finally:
                self.fix_finger_queue.task_done()
    
    def handle_update_finger(self):
        """Actualiza la tabla de fingers periódicamente."""
        while True:
            ip, port, id = self.update_finger_queue.get()
            try:
                ref = ChordNode(ip, port)
                self.fix_fingers(ref,id)
                print('Finger table updated!')
            finally:
                self.update_finger_queue.task_done()
                
    def request_succ_data(self, succ= False, pred = False):
        """Preguntar a mi sucesor por data."""
        if self.successor.id != self.id:
            if succ:
                response_succ = self.successor.request_data(self.id).decode()
                self.handler_data.create(response_succ)
          
        if pred:
            response_pred = self.predecessor.request_data(self.id).decode()
            self.handler_data.create(response_pred)
            
    def check_first(self)->bytes:
        """Chequear si soy el primer nodo."""
        while(True):
            self.first = True if self.predecessor == None or self.predecessor.id > self.id else False
    def set_leader(self):
        """Chequear si soy el último nodo."""
        while(True):
            self.leader = True if self.predecessor == None or self.successor.id < self.id else False    
        
    
    def find_first(self) -> bytes:
        """Buscar el primer nodo."""
        if self.leader:
            return f'{self.successor.ip}|{self.successor.port}'.encode()
    
        response = self.finger_table[-1].find_first()
        return response 
    def print_info(self):
        """Imprimir info mía y de mis adyacentes."""
        while True:
            time.sleep(10)
            print(f'my ip: {self.ip}\npred: {self.predecessor.ip if self.predecessor != None else None}, succ: {self.successor.ip}\n{"first" if self.first else "not first"}, {"leader" if self.leader else "not leader"}') 
            
    def _check_predecessor(self):
        while True:
          #si no estoy solo
          if self.predecessor != None:
            try:
              with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.connect((self.predecessor.ip, self.predecessor.port)) #nos conectamos x via TCP al predecesor
                s.settimeout(5) #configuramos el socket para lanzar un error si no recibe respuesta en 5 segundos
                s.sendall(CHECK_PREDECESSOR.encode('utf-8')) #chequeamos que no se ha caido el predecesor
                self.repli_pred = s.recv(1024).decode() #guardamos la info recibida
                ip_pred_pred = self.repli_pred.split('|')[-1] #guardamos el id del predecesor de nuestro predecesor

            except:
              #al no recibir respuesta, intuimos que se cayo y procedemos a guardar la data que nos envio
              print(f'Server {self.predecessor.ip} disconnected')
              self.handler_data.create(self.repli_pred)
              #le comunicamos al resto que se cayo el predecesor y pedimos que actuailice:
              #si somos el "first", significa que se cayo el lider, y se deben actualizar las "finger tables" con el predecesor del lider
              #de lo contrario, que se actualicen con nosotros
              self.broadcast.update_finger(self.predecessor.id, ip_pred_pred if self.first else self.ip, TCP_PORT)

              #nos aseguramos de que al menos habia 3 nodos
              if ip_pred_pred != self.ip:
                try:  
                  #tratamos de conectarnos con el predecesor de nuestro predecesor para comunicarle que se cayo su sucesor
                  #seguimos el mismo proceso
                  with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                    s.connect((ip_pred_pred, TCP_PORT))
                    s.settimeout(5)
                    s.sendall(f'{FALL_SUCC}|{self.ip}|{self.port_tcp}')
                    s.recv(1024).decode()

                except:
                  #en este punto, el predecesor de nuestro predecesor tambien se cayo, por lo que tambien salvamos sus datos
                  print(f'Server {ip_pred_pred} disconnected too')
                  self.handler_data.create(self.grandpa_data)

                  #si al menos somos 4, pregunto quien es el sucesor del nodo caid
                  if ip_pred_pred != self.successor.ip:
                    self.broadcast.notify(set_id(ip_pred_pred))

                  #eramos 3 nodos, por lo que al caerse 2, nos quedamos solos, por lo que toca resetearnos
                  else:
                    self.predecessor = None
                    self.successor = self.reference
                    self.finger_table = [self.reference] * 160

              #eramos 2 nodos, por lo que al caerse 1, nos quedamos solos, por lo que toca resetearnos
              else:
                self.predecessor = None
                self.successor = self.reference
                self.finger_table = [self.reference] * 160

            time.sleep(5)  
    
#region Sockets
    def start_tcp_server(self):
      """Iniciar el servidor TCP."""
      with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        s.bind((self.ip, self.port_tcp))
        print(f'Socket TCP binded to ({self.ip}, {self.port_tcp})')
        s.listen(10)

        while True:
          conn, addr = s.accept()
          client = threading.Thread(target=self._handle_client_tcp, args=(conn, addr))#!falta el handle
          client.start()
    
    def start_broadcast_server(self):
      """Iniciar el servidor UDP para broadcasting."""
      with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        s.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        s.bind(('', self.port_udp))
        print(f'Socket broadcast binded to {self.port_udp}')
    
        while True:
          data_recv = s.recvfrom(1024)
          thread = threading.Thread(target=self._handle_broadcast, args=(data_recv,))#!falta el handle
          thread.start()

    def start_udp_server(self):
      """Iniciar el servidor UDP."""
      with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        s.bind((self.ip, self.port_udp))
        print(f'Socket UDP binded to ({self.ip}, {self.port_udp})')

        while True:
          data_recv = s.recvfrom(1024)
          client = threading.Thread(target=self._handle_client_udp, args=(data_recv,))#!falta el handle
          client.start()
    #end region
    #region Protocols
    def handle_broadcast(self, data_recv: tuple):
      """Manejar varias peticiones en el socket UDP"""
      data = data_recv[0].decode().split('|')
      addr = data_recv[1]
      option = data[0]
      print(f'Recived data by broadcast: {data} from {addr[0] if self.ip != addr[0] else "myself"}')

      if option == JOIN:
        #si alguien solicito unirse, le envio su ubicacion si soy su responsable
        if addr[0] != self.ip:
          id = set_id(addr[0])
          #si estoy solo en la red soy tu sucesor y tu predecesor
          if self.predecessor == None:
            response = f'{self.ip}|{self.port_tcp}|{self.ip}|{self.port_tcp}'
            self.predecessor = ChordNode(addr[0], self.port_tcp)
            self.successor = ChordNode(addr[0], self.port_tcp)

          #si tu id es menor que el mio pero mayor que el de mi predecesor, entonces estas entre mi predecesor y yo
          #si eres menor que yo pero soy el "first", estas entre el "lider" y yo
          elif id < self.id and (id > self.predecessor.id or self.first):
            response = f'{self.predecessor.ip}|{self.predecessor.port}|{self.ip}|{self.port_tcp}'
            send_data(UPDATE_SUCC, self.predecessor.ip, self.port_udp, f'{ip}|{port}')
            self.predecessor = ChordNode(addr[0], self.port_tcp)

          #si eres mayor que yo pero yo soy el "lider", entonces estas entre el "first" y yo
          elif self.leader:
            response = f'{self.ip}|{self.port_tcp}|{self.successor.ip}|{self.successor.port}'
            send_data(UPDATE_PREDECESSOR, self.successor.ip, self.port_udp, f'{ip}|{port}')
            self.successor = ChordNode(addr[0], self.port_tcp)

          #enviar la ubicacion
          send_data(CONFIRM_JOIN, addr[0], self.port_udp, response)
    
        #si nadie me responde en 3 segundos, significa que estoy solo y termino el proceso de join
        else:
          time.sleep(2)

          if not self.joined_confirmed:
            self.joined = True

      elif option == FIX_FINGER:
        if addr[0] != self.ip:
          #si tenemos menor id que el nodo que se unio, ponemos en la cola su id  para actualizar nuestra "finger table"
          if self.id < set_id(addr[0]):
            self.fix_finger_queue.put((addr[0], TCP_PORT))

          #si tenemos mayor id, le decimos que nos ponga a nosotros en su finger table
          else:  
            send_data(FIX_FINGER, addr[0], UDP_PORT)

      elif option == NOTIFY:
        id = int(data[1])

        if addr[0] != self.ip:
          #si se cayo mi sucesor, me actualizo con quien lo notifico, le pido data si tiene y le comunico que se actualice conmigo
          if self.successor.id == id:
            self.successor = ChordNode(addr[0], self.port_tcp)
            self.request_succ_data(succ=True)
            send_data(UPDATE_PREDECESSOR, addr[0], UDP_PORT, f'{self.ip}|{self.port_tcp}')
            #si el nodo que me notifico tiene menor id que yo, que actualicen al nodo caido conmigo, pues soy el nuevo lider
            #en caso contrario, que actualicen con el nodo notificante
            self.broadcast.update_finger(id, self.ip if self.id > set_id(addr[0]) else addr[0], TCP_PORT)

      elif option == UPDATE_FINGER:
        id = int(data[1])
        ip = data[2]
        port = int(data[3])

        #si tengo menor id que el nodo que hay que actualizar, actualizo, ya que sale en mi "finger table"
        if self.id < id:
          self.update_finger_queue.put((ip, port, id))
          
    def _handle_client_udp(self, data_recv: tuple):
        data = data_recv[0].decode().split('|')
        addr = data_recv[1]
        print(f'Recived data in UDP socket: {data} from {addr[0]}')
        option = data[0]

        #al recibir la confirmacion del nodo "first", le solicito la union al anillo
        if option == CONFIRM_JOIN:
          self.join_confirmed = True

          #se la data no esta vacia me ubico 
          if len(data) != ['']:
            self.predecessor = ChordNode(data[1], int(data[2]))
            self.sucecessor = ChordNode(data[3], int(data[4]))
            self.joined = True

          #si la data esta vacia, hubo un error
          else:
            self.join_confirmed = False
            self.joined = False

        elif option == UPDATE_PREDECESSOR:
          ip = data[1]
          port = int(data[2])
          self.predecessor = ChordNode(ip, port)

        elif option == UPDATE_SUCC:
          ip = data[1]
          port = int(data[2])
          self.sucecessor = ChordNode(ip, port)

        elif option == DATA_PRED:
          data = data[1]
          self.grandpa_data = data

        elif option == FIX_FINGER:
          self.fix_finger_queue.put((addr[0], TCP_PORT))

