import socket

client = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)  # UDP

# Enable broadcasting mode
client.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)

client.bind(("", 37020))
while True:
    data, addr = client.recvfrom(1024)
    print(addr)
    print("received message: %s" % data)
    client.sendto(b'', (addr[0], 37021))
