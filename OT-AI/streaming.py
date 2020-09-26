import socket
import asyncio
import struct
import cv2
import pickle
import numpy as np
from datetime import datetime
import threading

try:
    from picamera.array import PiRGBArray
    from picamera import PiCamera
except:
    pass

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
    def __init__(self, host: str, port: int):
        self.host = host
        self.port = port
        self.on_frame_array = []

        self.package_size = struct.calcsize('L')
        self.data = b''
        self.lastFrame = None
        self.frameNum = 0

    async def serve(self):
        self.sock = await asyncio.start_server(self.server_handler, self.host, self.port)
        print("starting stream server...")
        await self.sock.serve_forever()

    async def server_handler(self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter):
        peername = writer.get_extra_info('peername')
        print("Stream connected", peername)

        startTime = datetime.now()
        dt = datetime.now() - startTime
        
        self.frameNum = 0

        while (datetime.now() - startTime).total_seconds() < 0.2:
            buf = []
            skip = False
            while(len(self.data) < self.package_size):
                print("phase 1", len(buf))
                buf = await reader.read(buffer_size)
                if len(buf) == 0:
                    skip = True
                    break
                self.data += buf

            # if no frame data then skip
            if skip:
                print("skipped 1")
                continue
            packed_msg_size = self.data[:self.package_size]

            # unpack data
            self.data = self.data[self.package_size:]
            msg_size = struct.unpack("L", packed_msg_size)[0]

            # recieve frame data
            while(len(self.data) < msg_size):
                buf = await reader.read(buffer_size)
                print("phase 2", len(buf))

                if len(buf) == 0:
                    skip = True
                    break
                self.data += buf

            # no frame data then skip
            if skip:
                print("skipped 2")
                continue

            frame_data = self.data[:msg_size]
            self.data = self.data[msg_size:]

            frame = pickle.loads(frame_data)
            startTime = datetime.now()
            self.lastFrame = frame
            self.call_on_frame(frame, writer)

        print("Peer disconnected", peername)
        cv2.destroyAllWindows()

    def call_on_frame(self, frame, writer: asyncio.StreamWriter):
        self.frameNum += 1
        print('recieved %dx%d image' % (frame.shape[1], frame.shape[0]))
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
    def __init__(self, host, port, usePiCam=False):
        self.host = host
        self.port = port
        self.clientsocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.on_msg_functions = []
        self.usePiCam = usePiCam

    async def connect(self):
        self.reader, self.writer = await asyncio.open_connection(self.host, self.port)
        print("starting stream client...")
        if self.usePiCam:
            print("stream client will use picamera")
        await self.client_handler()

    async def client_handler(self):
        if self.usePiCam:
            cam = picam()

        while True:
            if self.usePiCam:
                frame = cam.read()
            else:
                frame = self.get_frame()
            await self.send_frame(frame)
        
        print("client handler stopped")

    async def send_frame(self, frame):
        data = pickle.dumps(frame)
        self.writer.write(struct.pack("L", len(data)) + data)
        await self.writer.drain()
        print('sended %dx%d image' % (frame.shape[1], frame.shape[0]))

    def close(self):
        self.writer.close()

    def get_frame(self) -> np.ndarray:
        return self.get_frame_func()

    def on_get_frame(self):
        def decorator(f):
            self.get_frame_func = f
            return f
        return decorator


class picam:
    def __init__(self):
        self.frame = []
        self.isNew = False

        self.thread = threading.Thread(target=self.loop)
        self.thread.start()

    def read(self):
        while not self.isNew:
            pass
        return self.frame

    def loop(self):
        c = PiCamera()
        c.resolution = (640, 480)
        c.framerate = 32
        raw = PiRGBArray(c, size=(640, 480))

        while True:
            self.isNew = False
            c.capture(raw, format="bgr", use_video_port=True)
            self.frame = raw.array
            self.isNew = True
