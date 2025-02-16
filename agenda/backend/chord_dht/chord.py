import hashlib
import socket
import threading
import random
import time
import queue
from backend.chord_dht.utils import get_ip,set_id
from backend.chord_dht.communication import ADD_CONTACT, ADD_MEMBER, CANCEL_EVENT, CONFIRM_EVENT, CREATE_EVENT, CREATE_GROUP, LIST_CONTACTS, LIST_EVENTS, LIST_GROUP_AGENDA, LIST_GROUPS, LIST_PERSONAL_AGENDA, LOGIN, REMOVE_CONTACT, NodeReference, BroadcastRef,send_data
from backend.chord_dht.communication import JOIN,CONFIRM_JOIN,FIX_FINGER,FIND_FIRST,REQUEST_DATA,CHECK_PREDECESSOR,NOTIFY,UPDATE_PREDECESSOR,UPDATE_FINGER,UPDATE_SUCC,DATA_PRED,FALL_SUCC,REGISTER
from backend.chord_dht.handle_data import HandleData
from backend.chord_dht.storage import Database
TCP_PORT = 8000 #puerto de escucha del socket TCP
UDP_PORT = 8888 #puerto de escucha del socket UDP

class ChordNode:
    def __init__(self):
        self.ip = get_ip()
        self.port_udp = UDP_PORT
        self.port_tcp = TCP_PORT
        self.id = self._generate_id()
        self.reference= NodeReference(self.ip, self.port_tcp)
        self.predecessor = None
        self.successor = self.reference
        self.broadcast = BroadcastRef(self.port_udp)
        self.finger_table = [self.reference] * 160
        self.joined = False
        self.joined_confirmed= False
        self.db = Database()
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
          
#region Chord
    def _generate_id(self):
        """Genera un ID único basado en el hash de la IP y puerto."""
        node_info = f"{self.ip}"
        return int(hashlib.sha1(node_info.encode()).hexdigest(), 16) % (2 ** 160)
    
    def _closest_preceding_node(self, id):
        """Devuelve el nodo más cercano a un ID en la finger table."""
        for i in range(160):
            if self.id + (2**i) > id:
                return self.finger_table[i-1]
 
    def fix_fingers(self, node:NodeReference, id = None):
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
                ref = NodeReference(ip, port)
                self.fix_fingers(ref)
                print('Finger table fixed!')
            finally:
                self.fix_finger_queue.task_done()
    
    def handle_update_finger(self):
        """Actualiza la tabla de fingers periódicamente."""
        while True:
            ip, port, id = self.update_finger_queue.get()
            try:
                ref = NodeReference(ip, port)
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
        """Pedir data a mi predecesor cada 5 segundo para asegurar q no se ha caído. Maneja la caída de nodos"""
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
#end region  
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
          thread = threading.Thread(target=self.handle_broadcast, args=(data_recv,))#!falta el handle
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
            self.predecessor = NodeReference(addr[0], self.port_tcp)
            self.successor = NodeReference(addr[0], self.port_tcp)

          #si tu id es menor que el mio pero mayor que el de mi predecesor, entonces estas entre mi predecesor y yo
          #si eres menor que yo pero soy el "first", estas entre el "lider" y yo
          elif id < self.id and (id > self.predecessor.id or self.first):
            response = f'{self.predecessor.ip}|{self.predecessor.port}|{self.ip}|{self.port_tcp}'
            send_data(UPDATE_SUCC, self.predecessor.ip, self.port_udp, f'{ip}|{port}')
            self.predecessor = NodeReference(addr[0], self.port_tcp)

          #si eres mayor que yo pero yo soy el "lider", entonces estas entre el "first" y yo
          elif self.leader:
            response = f'{self.ip}|{self.port_tcp}|{self.successor.ip}|{self.successor.port}'
            send_data(UPDATE_PREDECESSOR, self.successor.ip, self.port_udp, f'{ip}|{port}')
            self.successor = NodeReference(addr[0], self.port_tcp)

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
            self.successor = NodeReference(addr[0], self.port_tcp)
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
            self.predecessor = NodeReference(data[1], int(data[2]))
            self.sucecessor = NodeReference(data[3], int(data[4]))
            self.joined = True

          #si la data esta vacia, hubo un error
          else:
            self.join_confirmed = False
            self.joined = False

        elif option == UPDATE_PREDECESSOR:
          ip = data[1]
          port = int(data[2])
          self.predecessor = NodeReference(ip, port)

        elif option == UPDATE_SUCC:
          ip = data[1]
          port = int(data[2])
          self.sucecessor = NodeReference(ip, port)

        elif option == DATA_PRED:
          data = data[1]
          self.grandpa_data = data

        elif option == FIX_FINGER:
          self.fix_finger_queue.put((addr[0], TCP_PORT))
          
    def _handle_client_tcp(self, conn: socket.socket, addr: tuple):
      data = conn.recv(1024).decode().split('|')
      option = data[0]

      if option == REGISTER:
          id = int(data[1])
          name = data[2]
          email = data[3]
          password = data[4]
          response = self.register(id, name, email, password)  # Procesar el registro
          conn.sendall(response.encode())  # Enviar respuesta al cliente
          
      elif option == LOGIN:
          # Iniciar sesión
          email = data[1]
          password = data[2]
          response = self.login(email, password)
      elif option == CREATE_EVENT:
          # Crear un evento
          event_id = int(data[1])
          name = data[2]
          date = data[3]
          owner_id = int(data[4])
          privacy = data[5]
          group_id = int(data[6]) if len(data) > 6 else None
          response = self.create_event(event_id, name, date, owner_id, privacy, group_id)
      elif option == CONFIRM_EVENT:
          # Confirmar un evento
          event_id = int(data[1])
          response = self.confirm_event(event_id)
      elif option == CANCEL_EVENT:
          # Cancelar un evento
          event_id = int(data[1])
          response = self.cancel_event(event_id)
      elif option == LIST_EVENTS:
          # Listar eventos de un usuario
          user_id = int(data[1])
          response = self.list_events(user_id)
      elif option == ADD_CONTACT:
          # Agregar un contacto
          user_id = int(data[1])
          contact_name = data[2]
          response = self.add_contact(user_id, contact_name)
      elif option == REMOVE_CONTACT:
          # Eliminar un contacto
          user_id = int(data[1])
          contact_name = data[2]
          response = self.remove_contact(user_id, contact_name)
      elif option == LIST_CONTACTS:
          # Listar contactos de un usuario
          user_id = int(data[1])
          response = self.list_contacts(user_id)
      elif option == CREATE_GROUP:
          # Crear un grupo
          group_id = int(data[1])
          name = data[2]
          owner_id = int(data[3])
          response = self.create_group(group_id, name, owner_id)
      elif option == ADD_MEMBER:
          # Agregar un miembro a un grupo
          group_id = int(data[1])
          user_id = int(data[2])
          response = self.add_member_to_group(group_id, user_id)
      elif option == LIST_GROUPS:
          # Listar grupos de un usuario
          user_id = int(data[1])
          response = self.list_groups(user_id)
      elif option == LIST_PERSONAL_AGENDA:
          # Listar agenda personal
          user_id = int(data[1])
          response = self.list_personal_agenda(user_id)
      elif option == LIST_GROUP_AGENDA:
          # Listar agenda grupal
          group_id = int(data[1])
          response = self.list_group_agenda(group_id)
      elif option == REQUEST_DATA:
        id = int(data[1])
        response = self.handler_data.data(True, id)
       
      elif option == CHECK_PREDECESSOR:
        response = (self.handler_data.data(False) + self.predecessor.ip)

        #si somos al menos 3 nodos, le mando a mi sucesor la data de mi predecesor
        if self.predecessor.id != self.successor.id:
          send_data(DATA_PRED, self.successor.ip, self.port_udp, self.repli_pred)

      elif option == FALL_SUCC:
        ip = data[1]
        port = int(data[2])
        self.successor = NodeReference(ip, port)
        response = f'ok'
        self.request_succ_data(succ=True) #pido data a mi sucesor al actualizar mi posicion
        send_data(UPDATE_PREDECESSOR, addr[0], UDP_PORT, f'{self.ip}|{self.port_tcp}') #si se cayo mi sucesor, le digo a su sucesor que soy su  nuevo predecesor 
      else:
          # Operación no reconocida
          response = "Invalid operation"
   

    # Enviar respuesta al cliente
      conn.sendall(response.encode())
      conn.close()
     
          
#end region
#region DB
    def register(self, id: int, name: str, email: str, password: str) -> str:
      if id < self.id and not self.first:
          # Reenviar al "first"
          first_node_data = self.find_first().decode().split('|')
          ip = first_node_data[0]
          port = int(first_node_data[1])
          first_node = NodeReference(ip, port)
          return first_node.register(id, name, email, password)
      else:
          # Registrar localmente
          return self._register(id, name, email, password)

    def _register(self, id: int, name: str, email: str, password: str) -> str:
        if (id < self.id) or (id > self.id and self.leader):
            # Registrar en la BD local
            success = self.db.register_user(name, email, password)
            return "User registered" if success else "Failed to register user"
        else:
            # Reenviar al nodo más cercano
            closest_node = self._closest_preceding_node(id)
            return closest_node.register(id, name, email, password)
          
    def create_event(self, event_id: int, name: str, date: str, owner_id: int, privacy: str, group_id=None) -> str:
      if event_id < self.id and not self.first:
          first_node_data = self.find_first().decode().split('|')
          ip = first_node_data[0]
          port = int(first_node_data[1])
          first_node = NodeReference(ip, port)
          return first_node.create_event(event_id, name, date, owner_id, privacy, group_id)
      else:
          return self._create_event(event_id, name, date, owner_id, privacy, group_id)

    def _create_event(self, event_id: int, name: str, date: str, owner_id: int, privacy: str, group_id=None) -> str:
        if (event_id < self.id) or (event_id > self.id and self.leader):
            success = self.db.create_event(name, date, owner_id, privacy, group_id)
            return  f"Event created: {name}" if success else f"Failed to create event {name}"
        else:
            closest_node = self._closest_preceding_node(event_id)
            return closest_node.create_event(event_id, name, date, owner_id, privacy, group_id)

    def confirm_event(self, event_id: int) -> str:
     if event_id < self.id and not self.first:
         first_node_data = self.find_first().decode().split('|')
         ip = first_node_data[0]
         port = int(first_node_data[1])
         first_node = NodeReference(ip, port)
         return first_node.confirm_event(event_id)
     else:
         return self._confirm_event(event_id)

    def _confirm_event(self, event_id: int) -> str:
        if (event_id < self.id) or (event_id > self.id and self.leader):
            success = self.db.confirm_event(event_id)
            return "Event confirmed" if success else "Failed to confirm event"
        else:
            closest_node = self._closest_preceding_node(event_id)
            return closest_node.confirm_event(event_id)
          
    def cancel_event(self, event_id: int) -> str:
      if event_id < self.id and not self.first:
         first_node_data = self.find_first().decode().split('|')
         ip = first_node_data[0]
         port = int(first_node_data[1])
         first_node = NodeReference(ip, port)
         return first_node.cancel_event(event_id)
      else:
          return self._cancel_event(event_id)

    def _cancel_event(self, event_id: int) -> str:
        if (event_id < self.id) or (event_id > self.id and self.leader):
            success = self.db.cancel_event(event_id)
            return "Event canceled" if success else "Failed to cancel event"
        else:
            closest_node = self._closest_preceding_node(event_id)
            return closest_node.cancel_event(event_id)
          
    def list_events(self, user_id: int) -> str:
      if user_id < self.id and not self.first:
         first_node_data = self.find_first().decode().split('|')
         ip = first_node_data[0]
         port = int(first_node_data[1])
         first_node = NodeReference(ip, port)
         return first_node.list_events(user_id)
      else:
          return self._list_events(user_id)

    def _list_events(self, user_id: int) -> str:
        if (user_id < self.id) or (user_id > self.id and self.leader):
            events = self.db.list_events(user_id)
            return "\n".join([str(event) for event in events])
        else:
            closest_node = self._closest_preceding_node(user_id)
            return closest_node.list_events(user_id)
          
    def add_contact(self, user_id: int, contact_name: str) -> str:
      if user_id < self.id and not self.first:
         first_node_data = self.find_first().decode().split('|')
         ip = first_node_data[0]
         port = int(first_node_data[1])
         first_node = NodeReference(ip, port)
         return first_node.add_contact(user_id, contact_name)
      else:
          return self._add_contact(user_id, contact_name)

    def _add_contact(self, user_id: int, contact_name: str) -> str:
        if (user_id < self.id) or (user_id > self.id and self.leader):
            success = self.db.add_contact(user_id, contact_name)
            return "Contact added" if success else "Failed to add contact"
        else:
            closest_node = self._closest_preceding_node(user_id)
            return closest_node.add_contact(user_id, contact_name)
          
    def remove_contact(self, user_id: int, contact_name: str) -> str:
      if user_id < self.id and not self.first:
         first_node_data = self.find_first().decode().split('|')
         ip = first_node_data[0]
         port = int(first_node_data[1])
         first_node = NodeReference(ip, port)
         return first_node.remove_contact(user_id, contact_name)
      else:
          return self._remove_contact(user_id, contact_name)

    def _remove_contact(self, user_id: int, contact_name: str) -> str:
        if (user_id < self.id) or (user_id > self.id and self.leader):
            success = self.db.remove_contact(user_id, contact_name)
            return "Contact removed" if success else "Failed to remove contact"
        else:
            closest_node = self._closest_preceding_node(user_id)
            return closest_node.remove_contact(user_id, contact_name)
          
    def list_contacts(self, user_id: int) -> str:
      if user_id < self.id and not self.first:
         first_node_data = self.find_first().decode().split('|')
         ip = first_node_data[0]
         port = int(first_node_data[1])
         first_node = NodeReference(ip, port)
         return first_node.list_contacts(user_id)
      else:
          return self._list_contacts(user_id)

    def _list_contacts(self, user_id: int) -> str:
        if (user_id < self.id) or (user_id > self.id and self.leader):
            contacts = self.db.list_contacts(user_id)
            return "\n".join(contacts)
        else:
            closest_node = self._closest_preceding_node(user_id)
            return closest_node.list_contacts(user_id)
          
    def create_group(self, group_id: int, name: str, owner_id: int) -> str:
      if group_id < self.id and not self.first:
         first_node_data = self.find_first().decode().split('|')
         ip = first_node_data[0]
         port = int(first_node_data[1])
         first_node = NodeReference(ip, port)
         return first_node.create_group(group_id, name, owner_id)
      else:
          return self._create_group(group_id, name, owner_id)

    def _create_group(self, group_id: int, name: str, owner_id: int) -> str:
        if (group_id < self.id) or (group_id > self.id and self.leader):
            success = self.db.create_group(name, owner_id)
            return "Group created" if success else "Failed to create group"
        else:
            closest_node = self._closest_preceding_node(group_id)
            return closest_node.create_group(group_id, name, owner_id)
          
    def add_member_to_group(self, group_id: int, user_id: int) -> str:
      if group_id < self.id and not self.first:
         first_node_data = self.find_first().decode().split('|')
         ip = first_node_data[0]
         port = int(first_node_data[1])
         first_node = NodeReference(ip, port)
         return first_node.add_member_to_group(group_id, user_id)
      else:
          return self._add_member_to_group(group_id, user_id)

    def _add_member_to_group(self, group_id: int, user_id: int) -> str:
        if (group_id < self.id) or (group_id > self.id and self.leader):
            success = self.db.add_member_to_group(group_id, user_id)
            return "Member added" if success else "Failed to add member"
        else:
            closest_node = self._closest_preceding_node(group_id)
            return closest_node.add_member_to_group(group_id, user_id)
    def list_personal_agenda(self, user_id: int) -> str:
      if user_id < self.id and not self.first:
         first_node_data = self.find_first().decode().split('|')
         ip = first_node_data[0]
         port = int(first_node_data[1])
         first_node = NodeReference(ip, port)
         return first_node.list_personal_agenda(user_id)
      else:
          return self._list_personal_agenda(user_id)

    def _list_personal_agenda(self, user_id: int) -> str:
        if (user_id < self.id) or (user_id > self.id and self.leader):
            agenda = self.db.list_personal_agenda(user_id)
            return "\n".join(agenda)
        else:
            closest_node = self._closest_preceding_node(user_id)
            return closest_node.list_personal_agenda(user_id)
          
    def list_group_agenda(self, group_id: int) -> str:
      if group_id < self.id and not self.first:
         first_node_data = self.find_first().decode().split('|')
         ip = first_node_data[0]
         port = int(first_node_data[1])
         first_node = NodeReference(ip, port)
         return first_node.list_group_agenda(group_id)
      else:
          return self._list_group_agenda(group_id)

    def _list_group_agenda(self, group_id: int) -> str:
        if (group_id < self.id) or (group_id > self.id and self.leader):
            agenda = self.db.list_group_agenda(group_id)
            return "\n".join(agenda)
        else:
            closest_node = self._closest_preceding_node(group_id)
            return closest_node.list_group_agenda(group_id)
#end region