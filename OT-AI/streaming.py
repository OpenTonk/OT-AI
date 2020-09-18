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
        while len(self.data) < self.p_size:
            buf = self.conn.recv(buffer_size)
            if len(buf) == 0:
                return False
            self.data += buf
        packed_msg_size = self.data[:self.p_size]

        # unpack data
        self.data = self.data[self.p_size:]
        msg_size = struct.unpack("L", packed_msg_size)[0]

        # reciever frame data
        while len(self.data) < msg_size:
            buf = self.conn.recv(buffer_size)
            if len(buf) == 0:
                return False
            self.data += buf
        frame_data = self.data[:msg_size]
        self.data = self.data[msg_size:]

        # convert to cv2 frame
        frame = pickle.loads(frame_data)
        # print(frame.size)

        return frame

class AsyncServer:
    def __init__(self, host, port):
        self.host = host
        self.port = port
        self.on_frame_array = []

        self.package_size = struct.calcsize('L')
        self.data = b''

    async def serve(self):
        self.sock = await asyncio.start_server(self.server_handler, self.host, self.port)
        await self.sock.serve_forever()

    async def server_handler(self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter):
        while True:
            while(len(self.data) < self.package_size):
                buf = await reader.read(buffer_size)
                if len(buf) == 0:
                    continue
                self.data += buf
            packed_msg_size = self.data[:self.package_size]

            # unpack data
            self.data = self.data[self.package_size:]
            msg_size = struct.unpack("L", packed_msg_size)[0]

            # recieve frame data
            while(len(self.data) < msg_size):
                buf = await reader.read(buffer_size)
                if len(buf) == 0:
                    continue
                self.data += buf
            frame_data = self.data[:msg_size]
            self.data = self.data[msg_size:]

            frame = pickle.loads(frame_data)
            self.call_on_frame(frame)

    
    def call_on_frame(self, frame):
        for func in self.on_frame_array:
            func(frame)

    def on_frame(self):
        def decorator(f):
            self.on_frame_array.append(f)
            return f
        return decorator
