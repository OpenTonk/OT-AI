import socket
import asyncio
import struct
import cv2
import pickle

buffer_size = 4096

class Server():
    def __init__(self, addr):
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.bind(addr)
        self.sock.listen(10)

        self.data = b''
        self.p_size = struct.calcsize('L')

    def wait_for_connection(self):
        self.conn, self.addr = self.sock.accept()
        return True

    def get_frame(self):
        

        #try:
            # recieve packed data
            while len(self.data) < self.p_size:
                self.data += self.conn.recv(buffer_size)
            packed_msg_size = self.data[:self.p_size]

            # unpack data
            self.data = self.data[self.p_size:]
            msg_size = struct.unpack("L", packed_msg_size)[0]

            # reciever frame data
            while len(self.data) < msg_size:
                self.data += self.conn.recv(buffer_size)
            frame_data = self.data[:msg_size]
            self.data = self.data[msg_size:]

            # convert to cv2 frame
            frame = pickle.loads(frame_data)
            # print(frame.size)

            return frame
        #except:
        #    return False




