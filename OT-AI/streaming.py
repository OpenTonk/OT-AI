import socket
import asyncio
import struct
import cv2
import pickle
import numpy as np
from datetime import datetime
import threading
import io

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
    def __init__(self, host: str, port: int, usePiCam=False):
        self.host = host
        self.port = port
        self.on_frame_array = []

        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        if usePiCam:
            self.socket = socket.socket()

        self.lastFrame = None
        self.frameNum = 0

        self.usePiCam = usePiCam

    async def serve(self):
        #self.sock = await asyncio.start_server(self.server_handler, self.host, self.port)
        
        print("starting stream server...")
        self.socket.bind((self.host, self.port))

        if self.usePiCam:
            self.socket.makefile('rb')
            print("stream server expects to recieve picam images")
        
        self.socket.listen(0)
        await self.server_handler()

    async def server_handler(self):
        while True:
            conn, info = self.socket.accept()

            print("Stream client connected", conn.getpeername())

            startTime = datetime.now()

            self.frameNum = 0

            if self.usePiCam:
                conn = conn.makefile('rb')
                package_size = struct.calcsize('<L')

                while (datetime.now() - startTime).total_seconds() < 0.2:
                    img_len = struct.unpack('<L', conn.read(package_size))[0]
                    
                    # disconnect when img length is 0
                    if not img_len:
                        break

                    # img stream to store img
                    img_stream = io.BytesIO()
                    img_stream.write(conn.read(img_len))

                    # rewind stream
                    img_stream.seek(0)

                    # convert to cv2 frame
                    data = np.fromstring(img_stream.getvalue(), dtype=np.uint8)
                    frame = cv2.imdecode(data, 1)

                    startTime = datetime.now()

                    # trigger on frame event
                    self.call_on_frame(frame)
            else:
                package_size = struct.calcsize('L')
                data = b''

                while (datetime.now() - startTime).total_seconds() < 0.2:
                    buf = []
                    skip = False
                    while(len(data) < package_size):
                        buf = conn.recv(buffer_size)
                        if len(buf) == 0:
                            skip = True
                            break
                        data += buf

                    # if no frame data then skip
                    if skip:
                        continue
                    packed_msg_size = data[:package_size]

                    # unpack data
                    data = data[package_size:]
                    msg_size = struct.unpack("L", packed_msg_size)[0]

                    # recieve frame data
                    while(len(data) < msg_size):
                        buf = conn.recv(buffer_size)

                        if len(buf) == 0:
                            skip = True
                            break
                        data += buf

                    # no frame data then skip
                    if skip:
                        continue

                    frame_data = data[:msg_size]
                    data = data[msg_size:]

                    frame = pickle.loads(frame_data)
                    
                    startTime = datetime.now()

                    self.call_on_frame(frame)

            cv2.destroyAllWindows()

    def call_on_frame(self, frame):
        self.frameNum += 1
        self.lastFrame = frame
        print("recieved frame", frame.size)

        for f in self.on_frame_array:
            f(frame)

    def on_frame(self):
        def decorator(f):
            self.on_frame_array.append(f)
            return f
        return decorator


class AsyncClient:
    def __init__(self, host, port, usePiCam=False):
        self.host = host
        self.port = port

        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        if usePiCam:
            self.socket = socket.socket()


        self.on_msg_functions = []
        self.usePiCam = usePiCam

    async def connect(self):
        print("starting stream client...")

        self.socket.connect((self.host, self.port))

        if self.usePiCam:
            print("stream client will use picamera")

        await self.client_handler()

    async def client_handler(self):
        if self.usePiCam:
            cam = PiCamera()
            cam.resolution = (640, 480)
            cam.framerate = 23

            # get file-like object connection
            conn = self.socket.makefile('wb')

            # get stream to store img
            stream = io.BytesIO()

            # read capture stream
            for img in cam.capture_continuous(stream, 'jpeg', use_video_port=True):
                # send image length
                conn.write(struct.pack('<L', stream.tell()))
                conn.flush()

                # rewind stream and send image data
                stream.seek(0)
                conn.write(stream.read())

                # reset stream
                stream.seek(0)
                stream.truncate()

        else:
            while True:
                frame = self.get_frame()
                
                data = pickle.dumps(frame)
                self.socket.sendall(struct.pack("L", len(data)) + data)
        
        print("client handler stopped")

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
        while len(self.frame) == 0:
            pass
        return self.frame

    def loop(self):
        c = PiCamera()
        c.resolution = (640, 480)
        c.framerate = 25
        raw = PiRGBArray(c)

        while True:
            raw.truncate(0)
            self.isNew = False
            raw.seek(0)
            c.capture(raw, format="bgr", use_video_port=True)
            self.frame = raw.array
            self.isNew = True
