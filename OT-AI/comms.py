import socket
import pickle

buffer_size = 16


class AsyncServer:
    def __init__(self, host: str, port: int):
        self.host = host
        self.port = port
        self.on_msg_listeners = []

        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

        self.disconnect = False
        self.i = 0

    async def serve(self):
        self.socket.bind((self.host, self.port))
        print("starting comms server...")
        self.socket.listen(1)
        await self.server_handler()

    def send_msg(self, msg):
        self.i += 1
        if True:
            data = pickle.dumps(msg)
            self.conn.send(bytes(f"{len(data):<{10}}", 'utf-8') + data)
            self.i = 0

    async def server_handler(self):
        conn, addr = self.socket.accept()
        self.conn = conn
        print("Peer connected", addr)

        while not self.disconnect:
            full_msg = b''
            new_msg = True

            while True:
                msg = conn.recv(buffer_size)
                if new_msg:
                    try:
                        msglen = int(msg[:10])
                    except ValueError:
                        pass
                    finally:
                        msglen = 0
                        new_msg = False
                
                if not new_msg: 
                    continue

                full_msg += msg

                if len(full_msg) - 10 == msglen:
                    recv = pickle.loads(full_msg[10:])
                    await self.call_on_msg(recv)
                    new_msg = True
                    full_msg = b""

        print("Peer disconnected", addr)
        conn.close()
        self.disconnect = False

    async def call_on_msg(self, msg):
        # arr = []
        for f in self.on_msg_listeners:
            await f(msg)
        # asyncio.gather(*arr)

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

    async def connect(self):
        self.socket.connect((self.host, self.port))
        print("starting comms client...")
        await self.client_handler()

    def send_msg(self, msg):
        data = pickle.dumps(msg)
        self.socket.send(bytes(f"{len(data):<{10}}", 'utf-8') + data)

    async def client_handler(self):
        full_msg = b''
        new_msg = True

        while True:
            msg = self.socket.recv(buffer_size)
            if new_msg:
                msglen = int(msg[:10])
                new_msg = False

            full_msg += msg

            if len(full_msg) - 10 == msglen:
                recv = pickle.loads(full_msg[10:])
                await self.call_on_msg(recv)
                new_msg = True
                full_msg = b""

    def close(self):
        self.socket.close()

    async def call_on_msg(self, msg):
        # arr = []
        for f in self.on_msg_listeners:
            await f(msg)
        # asyncio.gather(*arr)

    def on_msg(self):
        def decorator(f):
            self.on_msg_listeners.append(f)
            return f
        return decorator
