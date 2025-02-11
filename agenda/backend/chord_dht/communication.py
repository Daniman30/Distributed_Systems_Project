import socket
from backend.chord_dht.utils import set_id

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
ADD_MEMBER = 'add_member'
REMOVE_MEMBER = 'remove_member'
LIST_GROUPS = 'list_groups'
CREATE_EVENT = 'create_event'
CONFIRM_EVENT = 'confirm_event'
CANCEL_EVENT = 'cancel_event'
LIST_EVENTS = 'list_events'
BROADCAST_IP = '255.255.255.255'

class ChordNode:
    def __init__(self, ip: str, port: int):
        self.id = set_id(ip)
        self.ip = ip
        self.port = port
    
    def _send_data(self, op: str, data=None) -> bytes:
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.connect((self._ip, self._port))
                s.sendall(f'{op}|{data}'.encode('utf-8'))
                return s.recv(1024)
        except Exception as e:
            print(f"Error sending data: {e}")
            return b''
    
    def find_first(self):
        return self._send_data(FIND_FIRST)
    
    def request_data(self, id: int):
        return self._send_data(REQUEST_DATA, f'{id}')
    
    def notify(self, id: str):
        return self._send_data(NOTIFY, id)
    
    def update_finger(self, id: int, ip: str, port: int):
        return self._send_data(UPDATE_FINGER, f'{id}|{ip}|{port}')

class BroadcastRef:
    def __init__(self, port: int):
        self._port = port
    
    def _send_data(self, op: str, data=None) -> bytes:
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
                s.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
                s.sendto(f'{op}|{data}'.encode('utf-8'), (BROADCAST_IP, self._port))
        except Exception as e:
            print(f"Error sending data: {e}")
            return b''
    
    def join(self):
        self._send_data(JOIN)
    
    def fix_finger(self):
        self._send_data(FIX_FINGER)
    
    def notify(self, id: str):
        self._send_data(NOTIFY, id)
    
    def update_finger(self, id: int, ip: str, port: int):
        self._send_data(UPDATE_FINGER, f'{id}|{ip}|{port}')
def send_data(op: str, ip: str, port: int, data=None):
  try:
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
      s.sendto(f'{op}|{data}'.encode('utf-8'), (ip, port))
    
  except Exception as e:
    print(f"Error sending data: {e}")
    return b''