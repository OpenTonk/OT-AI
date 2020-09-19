import socket
import asyncio
import struct
import cv2
import pickle
import numpy as np
from datetime import datetime

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
        self.lastFrame = None

    async def serve(self):
        self.sock = await asyncio.start_server(self.server_handler, self.host, self.port)
        print("starting streamserver...")
        await self.sock.serve_forever()

    async def server_handler(self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter):
        peername = writer.get_extra_info('peername')
        print("Peer connected", peername)

        startTime = datetime.now()
        dt = datetime.now() - startTime

        while (datetime.now() - startTime).total_seconds() < 0.2:
            buf = []
            skip = False
            while(len(self.data) < self.package_size):
                buf = await reader.read(buffer_size)
                if len(buf) == 0:
                    skip = True
                    break
                self.data += buf

            # if no frame data then skip
            if skip:
                continue
            packed_msg_size = self.data[:self.package_size]

            # unpack data
            self.data = self.data[self.package_size:]
            msg_size = struct.unpack("L", packed_msg_size)[0]

            # recieve frame data
            while(len(self.data) < msg_size):
                buf = await reader.read(buffer_size)
                if len(buf) == 0:
                    skip = True
                    break
                self.data += buf

            # no frame data then skip
            if skip:
                continue

            frame_data = self.data[:msg_size]
            self.data = self.data[msg_size:]

            frame = pickle.loads(frame_data)
            startTime = datetime.now()
            self.lastFrame = frame
            self.call_on_frame(frame)

        print("Peer disconnected", peername)
        cv2.destroyAllWindows()

    def call_on_frame(self, frame):
        arr = []
        for f in self.on_frame_array:
            arr.append(f(frame))
        asyncio.gather(*arr)

    def on_frame(self):
        def decorator(f):
            self.on_frame_array.append(f)
            return f
        return decorator


class AsyncClient:
    def __init__(self, host, port):
        self.host = host
        self.port = port
        self.clientsocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    async def connect(self):
        self.reader, self.writer = await asyncio.open_connection(self.host, self.port)
        #self.clientsocket.connect((self.host, self.port))
        await self.client_handler()

    async def client_handler(self):
        while True:
            frame = self.get_frame()
            data = pickle.dumps(frame)
            self.writer.write(struct.pack("L", len(data)) + data)
            await self.writer.drain()
            #self.clientsocket.sendall(struct.pack("L", len(data)) + data)

    def close(self):
        self.writer.close()

    def get_frame(self):
        return self.get_frame_func()

    def on_get_frame(self):
        def decorator(f):
            self.get_frame_func = f
            return f
        return decorator
