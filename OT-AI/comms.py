import socket
import asyncio
import struct
import pickle

buffer_size = 4096


class AsyncServer:
    def __init__(self, host: str, port: int):
        self.host = host
        self.port = port
        self.on_msg_listeners = []

        self.package_size = struct.calcsize('L')
        self.data = b''

        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

        self.disconnect = False

    async def serve(self):
        self.socket.bind((self.host, self.port))
        print("starting comms server...")
        self.socket.listen(0)
        await self.server_handler()

    async def send_msg(self, msg):
        data = pickle.dumps(msg)
        self.socket.sendall(struct.pack("L", len(data)) + data)

    async def server_handler(self):
        peername = writer.get_extra_info('peername')
        print("Peer connected", peername)

        while not self.disconnect:
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

            msg_data = self.data[:msg_size]
            self.data = self.data[msg_size:]

            msg = pickle.loads(msg_data)
            self.call_on_msg(msg)

        print("Peer disconnected", peername)
        self.disconnect = False

    def call_on_msg(self, msg):
        arr = []
        for f in self.on_msg_listeners:
            arr.append(f(msg))
        asyncio.gather(*arr)

    def on_msg(self):
        def decorator(f):
            self.on_msg_listeners.append(f)
            return f
        return decorator

    def stop(self):
        self.disconnect = True


class AsyncClient:
    def __init__(self, host, port):
        self.host = host
        self.port = port

        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.on_msg_listeners = []

        self.package_size = struct.calcsize('L')
        self.data = b''

    async def connect(self):
        self.socket.connect((self.host, self.port))
        print("starting comms client...")
        await self.client_handler()

    def send_msg(self, msg):
        data = pickle.dumps(msg)
        self.socket.sendall(struct.pack("L", len(data)) + data)

    async def client_handler(self):
        while True:
            buf = []
            skip = False
            while(len(self.data) < self.package_size):
                buf = self.socket.recv(buffer_size)
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
                buf = self.socket.recv(buffer_size)
                if len(buf) == 0:
                    skip = True
                    break
                self.data += buf

            # no frame data then skip
            if skip:
                continue

            msg = self.data[:msg_size]
            self.data = self.data[msg_size:]
            self.call_on_msg(pickle.loads(msg))

    def close(self):
        self.writer.close()

    def call_on_msg(self, msg):
        arr = []
        for f in self.on_msg_listeners:
            arr.append(f(msg))
        asyncio.gather(*arr)

    def on_msg(self):
        def decorator(f):
            self.on_msg_listeners.append(f)
            return f
        return decorator
