import cv2
import asyncio
from streaming import AsyncClient
import comms
import threading
from picamera.array import PiRGBArray
from picamera import PiCamera
import time

isPi = False

# cap = cv2.VideoCapture('video.mp4')
if isPi:
    cam = PiCamera()
    #cam.resolution = (640, 480)
    #cam.framerate = 30
    rawCapture = PiRGBArray(cam)

else:
    cap = cv2.VideoCapture(-1)

client = AsyncClient('192.168.111.106', 8084)
size = 1

comms = comms.AsyncClient('192.168.111.106', 8085)

time.sleep(0.1)


@client.on_get_frame()
def read_frame():
    if isPi:
        ret = True
        cam.capture(rawCapture, format="bgr")
        frame = rawCapture.array
    else:
        ret, frame = cap.read()

    if ret:
        h, w, _ = frame.shape
        frame = cv2.resize(frame, (int(w / size), int(h / size)))
        return frame


@comms.on_msg()
async def on_msg(msg):
    print(msg)


def comms_thread():
    asyncio.run(comms.connect())


# start comms client on separate thread
t = threading.Thread(target=comms_thread)
t.start()

asyncio.run(client.connect())
