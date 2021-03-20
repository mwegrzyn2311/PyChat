from tkinter import *
import threading
import socket
from tkinter.filedialog import *
from PIL import Image, ImageTk
import io

serverIP = "127.0.0.1"
serverPort = 9009

MULTICAST_GROUP = '224.1.1.1'#'224.1.1.1'
MULTICAST_PORT = 5007

class ClientChatApp(Frame):
    def __init__(self, client_name, tcp_socket, udp_socket, udp_multicast_send_socket, udp_multicast_recv_socket, **kw):
        Frame.__init__(self, master=None)
        self.name = client_name
        self.tcp_socket = tcp_socket
        self.udp_socket = udp_socket
        self.udp_multicast_send_socket = udp_multicast_send_socket
        self.udp_multicast_recv_socket = udp_multicast_recv_socket
        self.messages = []
        self.received_images = []
        self.pack()
        self.create_widgets()
        self.setup_receive_thread()
        self.master.protocol("WM_DELETE_WINDOW", self.on_chat_window_closing)

    def on_chat_window_closing(self):
        self.tcp_socket.sendall(bytes("CLIENT_EXIT", 'utf-8'))
        self.udp_socket.close()
        self.master.destroy()

    def send_msg(self, event=None):
        self.tcp_socket.sendall(bytes(self.msg_field.get(), 'utf-8'))
        self.msg_field.delete(0, 'end')

    def send_image(self):
        self.imageButton.pack_forget()
        delattr(self, 'imageButton')
        self.mutlicast_button["state"] = "disabled"
        img_byte_arr = io.BytesIO()
        self.image.save(img_byte_arr, format='PNG')
        img_byte_arr = img_byte_arr.getvalue()
        self.udp_socket.sendto(img_byte_arr, (serverIP, serverPort))

    def send_image_multicast(self):
        if not hasattr(self, 'imageButton'):
            return
        self.imageButton.pack_forget()
        self.mutlicast_button["state"] = "disabled"
        delattr(self, 'imageButton')
        img_byte_arr = io.BytesIO()
        self.image.save(img_byte_arr, format='PNG')
        img_byte_arr = img_byte_arr.getvalue()
        print("Sending...")
        self.udp_multicast_send_socket.sendto(bytes(self.name, 'utf-8'), (MULTICAST_GROUP, MULTICAST_PORT))
        self.udp_multicast_send_socket.sendto(img_byte_arr, (MULTICAST_GROUP, MULTICAST_PORT))

    def setup_receive_thread(self):
        def response_fn():
            while True:
                response = self.tcp_socket.recv(1024).decode('utf-8')
                print(f"Received \"{response}\"")
                # Obsługa zamknięcia socketa po stronie servera
                if response == "":
                    print("Closing TCP connection with the server...")
                    self.tcp_socket.close()
                    return
                sender, id, color, msg = response.split(" | ")
                shown_msg = sender + "[" + id + "]: " + msg
                self.put_new_msg(shown_msg, color, sender)

        def udp_response_fn():
            while True:
                info_msg = self.udp_socket.recv(1024).decode('utf-8')
                sender, id, color = info_msg.split(" | ")
                msg = self.udp_socket.recv(1048576)
                self.put_new_image(sender, id, color, msg)

        def udp_multicast_response_fn():
            while True:
                sender = self.udp_multicast_recv_socket.recv(1024).decode('utf-8')
                msg = self.udp_multicast_recv_socket.recv(1048576)
                self.put_new_image(sender, "M", "#336699", msg)

        self.response_thread = threading.Thread(target=response_fn, args=())
        self.response_thread.daemon = True
        self.response_thread.start()
        self.udp_response_thread = threading.Thread(target=udp_response_fn, args=())
        self.udp_response_thread.daemon = True
        self.udp_response_thread.start()
        self.udp_multicast_response_thread = threading.Thread(target=udp_multicast_response_fn, args=())
        self.udp_multicast_response_thread.daemon = True
        self.udp_multicast_response_thread.start()

    def on_new_widget_added(self):
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))
        self.canvas.yview_moveto('1.0')

    def put_new_image(self, sender, id, color, data):
        shown_msg = sender + "[" + id + "]: "
        new_img = PhotoImage(data=data)
        self.received_images.append(new_img)
        new_image_frame = Frame(self.messages_frame, bg=color)
        sender_text = Label(new_image_frame, text=shown_msg, bg=color, width=10, height=1, font=("Courier", 15))
        sender_text.grid(padx=5, pady=(5, 1), sticky=N+S+W+E, row=0, column=0)
        new_image = Label(new_image_frame, image=new_img)
        new_image.grid(padx=5, pady=(1, 5), sticky=N+S+W+E, row=1, column=0)

        if sender == self.name:
            new_image_frame.grid(padx=(100, 0), pady=5, sticky=N+S+W+E)
        else:
            new_image_frame.grid(padx=(0, 100), pady=5, sticky=N+S+W+E)
        self.on_new_widget_added()

    def put_new_msg(self, msg_text, msg_color, author_name):
        msg_label = Text(self.messages_frame, bg=msg_color, width=40, height=2, font=("Courier", 15), wrap=WORD)
        msg_label.insert(1.0, msg_text)
        msg_label["state"] = "disabled"

        if author_name == self.name:
            msg_label.grid(padx=(100, 0), pady=5, sticky=N+S+W+E)
        else:
            msg_label.grid(padx=(0, 100), pady=5, sticky=N+S+W+E)
        self.messages.append(msg_label)
        self.on_new_widget_added()

    def open_image_picker(self):
        filename = askopenfile(filetypes=[("Images", ".jpg .png")])
        print(filename.name)
        self.image = Image.open(filename.name)
        max_size = 300
        if self.image.width >= max_size or self.image.height >= max_size:
            if self.image.width > self.image.height:
                self.image = self.image.resize((max_size, int(self.image.height/self.image.width * max_size)))
            else:
                self.image = self.image.resize((int(self.image.width / self.image.height * max_size), max_size))
        self.img = ImageTk.PhotoImage(self.image)
        if not hasattr(self, 'imageButton'):
            self.imageButton = Button(self, image=self.img, command=self.send_image)
            self.imageButton.pack()
            self.mutlicast_button["state"] = "normal"
        else:
            self.imageButton.configure(image=self.img)

    def create_widgets(self):
        self.container = Frame(self, width=750, height=500)
        self.canvas = Canvas(self.container, width=700, height=500)
        self.scrollbar = Scrollbar(self.container, orient="vertical", command=self.canvas.yview)

        self.messages_frame = Frame(self.canvas)

        def on_mousewheel(e):
            self.canvas.yview_scroll(int(-1*(e.delta/120)), "units")

        self.canvas.bind("<MouseWheel>", on_mousewheel)

        self.canvas.create_window((0, 0), window=self.messages_frame, anchor="nw")
        self.canvas.configure(yscrollcommand=self.scrollbar.set)
        self.container.pack()
        self.canvas.pack(side="left", fill="both", expand=True)
        self.scrollbar.pack(side="right", fill="y")

        self.msg_field = Entry(self, font=("Courier", 15), width=40)
        self.msg_field.bind("<Return>", self.send_msg)
        self.msg_field.pack()

        self.button_container = Frame(self)

        self.image_picker = Button(self.button_container, command=self.open_image_picker, text="Choose image")
        self.image_picker.grid(row=0, column=0)
        self.mutlicast_button = Button(self.button_container, command=self.send_image_multicast, text="Multicast Send", state="disabled")
        self.mutlicast_button.grid(row=0, column=1)

        self.button_container.pack()
