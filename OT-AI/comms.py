import socket
import asyncio
import struct
import pickle

buffer_size = 4096


class AsyncServer:
    def __init__(self, host: str, port: int):
        self.host = host
        self.port = port
        self.on_frame_array = []

        self.package_size = struct.calcsize('L')
        self.data = b''
        self.lastFrame = None

    async def serve(self):
        self.sock = await asyncio.start_server(self.server_handler, self.host, self.port)
        print("starting stream server...")
        await self.sock.serve_forever()

    def send_msg(self, writer: asyncio.StreamWriter, msg: str):
        writer.write(msg.encode('utf8'))

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
            self.call_on_frame(frame, writer)

        print("Peer disconnected", peername)
        cv2.destroyAllWindows()

    def call_on_frame(self, frame: np.ndarray, writer: asyncio.StreamWriter):
        arr = []
        for f in self.on_frame_array:
            arr.append(f(frame, writer))
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
        self.on_msg_listeners = []
        self.data = b''

    async def connect(self):
        self.reader, self.writer = await asyncio.open_connection(self.host, self.port)
        print("starting comms client...")
        await self.client_handler()

    async def send_msg(self, msg):
        data = pickle.dumps(msg)
        self.writer.write(struct.pack("L", len(data)) + data)
        await self.writer.drain()

    async def client_handler(self):
        while True:
            buf = []
            skip = False
            while(len(self.data) < self.package_size):
                buf = await self.reader.read(buffer_size)
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
                buf = await self.reader.read(buffer_size)
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
