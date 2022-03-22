#!/usr/bin/python
import socket
import select
import time
import sys


class bcolors:
    HEADER = "\033[95m"
    OKBLUE = "\033[94m"
    OKCYAN = "\033[96m"
    OKGREEN = "\033[92m"
    WARNING = "\033[93m"
    FAIL = "\033[91m"
    ENDC = "\033[0m"
    BOLD = "\033[1m"
    UNDERLINE = "\033[4m"


buffer_size = 4096
delay = 0.0001
proxy_port = 443 # !!! listen port 

# **************************************
# server_name = "SOLANA LOCAL HOST TEST VALIDATOR"
# forward_to = ('127.0.0.1', 8900)
server_name = "SOLANA DEVNET"
forward_to = ("139.178.65.155", 443) # input IP before start


class Forward:
    def __init__(self):
        self.forward = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    def start(self, host, port):
        try:
            self.forward.connect((host, port))
            return self.forward
        except Exception as e:
            print(e)
            return False


class ProxyServer:
    input_list = []
    channel = {}
    channel_name = {}

    def __init__(self, host, port):
        self.server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.server.bind((host, port))
        self.server.listen(200)

    def main_loop(self):
        self.input_list.append(self.server)
        while 1:
            inputready, outputready, exceptready = select.select(self.input_list, [], [])
            for self.s in inputready:
                if self.s == self.server:
                    self.on_accept()
                    break

                self.data = self.s.recv(buffer_size)
                if len(self.data) == 0:
                    self.on_close()
                    break
                else:
                    self.on_recv()

    def on_accept(self):
        forward = Forward().start(forward_to[0], forward_to[1])
        client_socket, client_address = self.server.accept()
        if forward:
            print(client_address, "has connected")
            self.input_list.append(client_socket)
            self.input_list.append(forward)
            self.channel[client_socket] = forward
            self.channel_name[client_socket] = "Client"
            self.channel[forward] = client_socket
            self.channel_name[forward] = "Route"
        else:
            print("Can't establish connection with remote server.")
            print("Closing connection with client side", client_address)
            client_socket.close()

    def on_close(self):
        print(self.s.getpeername(), "has disconnected")
        # remove objects from input_list
        self.input_list.remove(self.s)
        self.input_list.remove(self.channel[self.s])
        out = self.channel[self.s]
        # close the connection with client
        self.channel[out].close()  # equivalent to do self.s.close()
        # close the connection with remote server
        self.channel[self.s].close()
        # delete both objects from channel dict
        del self.channel[out]
        del self.channel[self.s]

    def on_recv(self):
        data = self.data
        # here we can parse and/or modify the data before send forward
        print(
            bcolors.OKGREEN + "MESSAGE FROM: ", self.channel_name[self.s] + bcolors.ENDC
        )
        print(bcolors.OKCYAN)
        print(data)
        print(bcolors.ENDC)

        time.sleep(delay)
        print(bcolors.OKBLUE + "Sending..." + bcolors.ENDC)
        self.channel[self.s].send(data)


if __name__ == "__main__":
    server = ProxyServer("", proxy_port)

    print(bcolors.BOLD)
    print("Server Port: ", proxy_port)
    print("Forward to: ", forward_to)
    print("SERVER", server_name)
    print(bcolors.ENDC)

    print("Ready to accept transactions")
    print("****************************")
    try:
        server.main_loop()
    except KeyboardInterrupt:
        print("Ctrl C - Stopping server")
        sys.exit(1)
