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


class AsyncServer:
    def __init__(self, host: str, port: int, usePiCam=False):
        self.host = host
        self.port = port

        self.on_frame_array = []
        self.on_disconnect_array = []

        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        if usePiCam:
            self.socket = socket.socket()

        self.lastFrame = None
        self.frameNum = 0

        self.usePiCam = usePiCam

        self.frame = []

    async def serve(self):
        # self.sock = await asyncio.start_server(self.server_handler, self.host, self.port)

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
                cam = PiCameraThread(conn)

                t = threading.Thread(target=cam.loop)
                t.start()

                await asyncio.sleep(2)

                while t.is_alive():
                    #start = datetime.now()
                    if not np.array_equal(self.lastFrame, cam.frame):
                        self.call_on_frame(cam.frame)
                    
                    #print((datetime.now() - start).total_seconds())
                    #await asyncio.sleep(0.05)
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

            print("Stream client disconnected", conn.getpeername())
            cv2.destroyAllWindows()
            self.call_on_disconnect()

    def call_on_frame(self, frame):
        self.frameNum += 1
        self.lastFrame = frame

        for f in self.on_frame_array:
            f(frame)

    def call_on_disconnect(self):
        for f in self.on_disconnect_array:
            f()

    def on_frame(self):
        def decorator(f):
            self.on_frame_array.append(f)
            return f
        return decorator

    def on_disconnect(self):
        def decorator(f):
            self.on_disconnect_array.append(f)
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
            cam.resolution = (360, 270)
            cam.framerate = 23

            # get file-like object connection
            conn = self.socket.makefile('wb')

            # get stream to store img
            stream = io.BytesIO()

            # read capture stream
            try:
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
            finally:
                conn.write(struct.pack('<L', 0))
                conn.flush()
                conn.close()
                self.socket.close()
                cam.stop_recording()
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


class PiCameraThread:
    def __init__(self, conn):
        self.frame = []
        self.conn = conn.makefile('rb')

    def loop(self):
        package_size = struct.calcsize('<L')
        img_stream = io.BytesIO()

        try:
            while True:
                start = datetime.now()
                img_len = struct.unpack('<L', self.conn.read(package_size))[0]

                # disconnect when img length is 0
                if not img_len:
                    break

                # img stream to store img
                img_stream.write(self.conn.read(img_len))

                # rewind stream
                img_stream.seek(0)

                # convert to cv2 frame
                data = np.fromstring(img_stream.getvalue(), dtype=np.uint8)
                self.frame = cv2.imdecode(data, 1)
                
                # reset stream
                img_stream.seek(0)
                img_stream.truncate()
                # print((datetime.now() - start).total_seconds())
        finally:
            return 0
