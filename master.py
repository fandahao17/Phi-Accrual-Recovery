import socket
import threading
import time
from datetime import datetime
from phi_accrual_failure_detector import PhiAccrualFailureDetector

fd = PhiAccrualFailureDetector(16, 50, 500, 0, 1000)
server = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)

# Enable broadcasting mode
server.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
server.bind(("", 37022))

listenfd = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)

# Enable broadcasting mode
listenfd.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
listenfd.bind(("", 37021))

def thread_fn():
    while True:
        data, addr = listenfd.recvfrom(1024)
        fd.heartbeat(datetime.now())


threading.Thread(target=thread_fn).start()
message = b""
while True:
    print('Phi is {}'.format(fd.phi(datetime.now())))
    time.sleep(1)
    server.sendto(message, ("255.255.255.255", 37020))
