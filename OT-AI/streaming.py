import socket
import asyncio
import struct
import cv2
import pickle
import numpy as np
from datetime import datetime

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

    def send_msg(self, writer: asyncio.StreamWriter, msg: str):
        writer.write(msg.encode('utf8'))

    async def server_handler(self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter):
        peername = writer.get_extra_info('peername')
        print("Peer connected", peername)

        startTime = datetime.now()
        dt = datetime.now() - startTime
        
        self.frameNum = 0

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
        self.frameNum += 1
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
            cam = PiCamera()
            cam.resolution = (640, 480)
            cam.framerate = 30
            rawCapture = PiRGBArray(cam, size=(640, 480))
            await asyncio.sleep(0.1)
            
            for frame in cam.capture_continuous(rawCapture, format="bgr", use_video_port=True):
                img = frame.array
                await self.send_frame(img)
                rawCapture.truncate(0)
        else:
            while True:
                frame = self.get_frame()
                await self.send_frame(frame)

    async def send_frame(self, frame):
        data = pickle.dumps(frame)
        self.writer.write(struct.pack("L", len(data)) + data)
        await self.writer.drain()

    def close(self):
        self.writer.close()

    def get_frame(self) -> np.ndarray:
        return self.get_frame_func()

    def on_get_frame(self):
        def decorator(f):
            self.get_frame_func = f
            return f
        return decorator
