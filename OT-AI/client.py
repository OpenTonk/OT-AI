import cv2
import asyncio
from streaming import AsyncClient
import comms
import threading

# cap = cv2.VideoCapture('video.mp4')
cap = cv2.VideoCapture(-1)
client = AsyncClient('192.168.111.106', 8084)
size = 1

comms = comms.AsyncClient('192.168.111.106', 8085)


@client.on_get_frame()
def read_frame():
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
