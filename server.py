import socket
import threading

serverIP = "127.0.0.1"
serverPort = 9009
serverTcpSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
serverTcpSocket.bind((serverIP, serverPort))
serverTcpSocket.listen(5)

serverUdpSocket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
serverUdpSocket.bind((serverIP, serverPort))

tcpClients = []
clientAddresses = []
clientNames = []
colors = ["#00cc00", "#ffcc00", "#00ccff", "#ff6699", "#cc6600", "#669999"]

id = 1

print('SERVER')


def client_thread_fn(id, name, socket):
    try:
        print(f"Connection from {id, name, socket}")

        while True:
            msg = socket.recv(1024).decode('utf-8')
            if msg == "CLIENT_EXIT":
                return
            print(f"Received message {msg} from {name}[{id}] via TCP")
            for client in tcpClients:
                client.send(bytes(name + " | " + str(id) + " | " + colors[id % len(colors)] + " | " + msg, 'utf-8'))
    finally:
        print(f"Closing the connection with {id, name, socket}")
        tcpClients.remove(socket)
        socket.close()


def client_thread(id, name, socket):
    return threading.Thread(target=client_thread_fn, args=(id, name, socket,))

def udp_thread_fn():
    try:
        print("Udp connection started")

        while True:
            (msg, sender_addr) = serverUdpSocket.recvfrom(1048576)
            print(f"Received message {msg} via UDP")
            index = clientAddresses.index(sender_addr)
            info_msg = bytes(clientNames[index] + " | " + str(index+1) + " | " + colors[(index+1) % len(colors)], 'utf-8')
            for addr in clientAddresses:
                # Start by sending sender info
                serverUdpSocket.sendto(info_msg, addr)
                # Then send the image
                serverUdpSocket.sendto(msg, addr)

    finally:
        print(f"Closing the Udp connection with {id, name}")


def udp_thread():
    return threading.Thread(target=udp_thread_fn, args=())


ut = udp_thread()
ut.daemon = True
ut.start()
while True:
    # Accept connections
    print("Waiting for connection...")
    (clientSocket, address) = serverTcpSocket.accept()
    print(address)
    tcpClients.append(clientSocket)
    clientAddresses.append(address)
    name = clientSocket.recv(1024).decode('utf-8')
    clientNames.append(name)
    ct = client_thread(id, name, clientSocket)
    ct.daemon = True
    ct.start()

    clientSocket.send(bytes('Server | 0 | #ffffff | Succesfully connected to the server', 'utf-8'))
    id += 1
