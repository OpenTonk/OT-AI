import cv2
import asyncio
from streaming import AsyncClient
import comms
import threading
import sys, getopt


ip = "127.0.0.1"
port = 8084
usePiCam = False
size = 1

try:
    opts, args = getopt.getopt(sys.argv[1:], "ha:p:s:", ["ip=", "port=", "size=", "usepicam"])
except getopt.GetoptError:
    print("ERROR: client.py -a <server ip> -p <port> -s <size> (--usepicam)")
    exit()

for opt, arg in opts:
    if opt == '-h':
        print("client.py -a <server ip> -p <port> -s <size> (--usepicam)")
        exit()
    elif opt in ("-a", "--ip"):
        ip = arg
    elif opt in ("-p", "--port"):
        port = int(arg)
    elif opt in ("-s", "--size"):
        size = int(arg)
    elif opt == '--usepicam':
        usePiCam = True

if not usePiCam:
    cap = cv2.VideoCapture(0)

client = AsyncClient(ip, port, usePiCam)

comms = comms.AsyncClient(ip, port + 1)

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
