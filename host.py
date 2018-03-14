import socket
import threading
import math
import time
import struct
import json

import sys

import pygame
from pygame.locals import *


global serversocket

fps = 60
gap = 1 / fps

loop = True

class Connection(threading.Thread):
    def __init__(self, conn):
        threading.Thread.__init__(self)
        self.conn = conn
        self.data = ""

        self.daemon = True
        self.start()

    def run(self):
        while True:
            try:
                self.data = self.recv_msg().decode()
                if self.data != "":

                    rec = json.loads(self.data)

                    if rec["com"] == "data":
                        print(rec["data"])
                    elif rec["com"] == "exit":
                        global loop
                        loop = False
                        self.conn.close()
                        break

            except socket.error as e:
#                    if e.errno == errno.ECONNRESET:
                self.conn.close()
                break
            except Exception as e:
                raise (e)

    def send_msg(self, msg):
        try:
            msg = struct.pack('>I', len(msg)) + msg
            self.conn.sendall(msg)
        except socket.error as e:
            print("disconnected")
            #                if e.errno == errno.ECONNRESET:
            self.conn.close()

    def send_set(self, s):
        def set_default(obj):
            if isinstance(obj, set):
                return list(obj)
            raise TypeError

        data = json.dumps(s, default=set_default)
        self.send_msg(data.encode())

    def recv_msg(self):
        # Read message length and unpack it into an integer
        raw_msglen = self.recvall(4)
        if not raw_msglen:
            return None
        msglen = struct.unpack('>I', raw_msglen)[0]
        # Read the message data
        return self.recvall(msglen)

    def recvall(self, n):
        # Helper function to recv n bytes or return None if EOF is hit
        data = b''
        while len(data) < n:
            packet = self.conn.recv(n - len(data))
            if not packet:
                return None
            data += packet
        return data



class Host(threading.Thread):
    def __init__(self):
        super(Host, self).__init__()
        self.s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.s.bind(('localhost', 8089))
        self.s.listen(5)  # become a server socket, maximum 5 connections
        self.lock = threading.Lock()

        pygame.init()
        self.joystickO = pygame.joystick.Joystick(0)
        self.joystickO.init()

        self.daemon = True
        self.start()

    def run(self):
        while True:
            conn, address = self.s.accept()
            self.connection = Connection(conn)


    def sync(self):
            temp = {
                "com":"data",
                "data":[self.joystickO.get_axis(0), self.joystickO.get_axis(3)]
            }

            self.connection.send_set(temp)



if __name__ == '__main__':

    host = Host()

    lastCheck = 0

    while loop:
        host.sync()

        now = time.time()
        wait = (lastCheck + gap) - now
        lastCheck = now
        if wait > 0:
            time.sleep(wait)


