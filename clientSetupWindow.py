from tkinter import *
from clientChatWindow import *
import socket
import struct

serverIP = "127.0.0.1"
serverPort = 9009

MULTICAST_GROUP = '224.1.1.1'
MULTICAST_PORT = 5007


class Application(Frame):
    def connect(self):
        tcp_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        tcp_sock.connect((serverIP, serverPort))
        # Send name info to the server
        name = self.name_field.get()
        tcp_sock.send(bytes(name, 'utf-8'))
        # Create udp socket
        udp_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        udp_sock.bind(('', tcp_sock.getsockname()[1]))
        # Create udp multicast sockets
        udp_multicast_send_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
        udp_multicast_send_sock.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_TTL, 32)

        udp_multicast_recv_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)

        udp_multicast_recv_sock.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_TTL, 32)
        udp_multicast_recv_sock.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_LOOP, 1)
        udp_multicast_recv_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        udp_multicast_recv_sock.bind(('', MULTICAST_PORT))
        host = socket.gethostbyname(socket.gethostname())
        udp_multicast_recv_sock.setsockopt(socket.SOL_IP, socket.IP_MULTICAST_IF, socket.inet_aton(host))
        udp_multicast_recv_sock.setsockopt(socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP, socket.inet_aton(MULTICAST_GROUP) + socket.inet_aton(host))

        # Open chat window
        self.master.destroy()
        self.master = Tk()
        self.app = ClientChatApp(name, tcp_sock, udp_sock, udp_multicast_send_sock, udp_multicast_recv_sock)
        self.master.mainloop()


    def createWidgets(self):
        self.name_label = Label(self, text="Name").grid(row=0)

        self.name_field = Entry(self)
        self.name_field.grid(row=0, column=1)

        self.connect_button = Button(self)
        self.connect_button["text"] = "Connect",
        self.connect_button["bg"] = "#00cc00"
        self.connect_button["command"] = self.connect
        self.connect_button.grid(row=1, column=0)

        self.QUIT = Button(self)
        self.QUIT["text"] = "QUIT"
        self.QUIT["bg"] = "#cc0000"
        self.QUIT["fg"] = "#eeeeee"
        self.QUIT["command"] = self.quit
        self.QUIT.grid(row=1, column=1)



    def __init__(self):
        Frame.__init__(self, master=None)
        self.pack()
        self.createWidgets()

root = Tk()
app = Application()
root.mainloop()
