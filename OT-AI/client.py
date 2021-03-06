import asyncio
from streaming import AsyncClient
import comms
import threading
import sys
import getopt
import tankcontrol


ip = "127.0.0.1"
port = 8084
usePiCam = False
size = 1
controller = tankcontrol.TankControl((11, 12), (15, 16))
disableMotor = False

try:
    opts, args = getopt.getopt(sys.argv[1:], "ha:p:s:", [
                               "ip=", "port=", "size=", "usepicam", "disablemotor"])
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
    elif opt == '--disablemotor':
        disableMotor = True

if not usePiCam:
    import cv2
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
    #print(msg)
    if "speed" in msg and "angle" in msg and not disableMotor:
        controller.drive(msg["speed"], msg["angle"])


def comms_thread():
    asyncio.run(comms.connect())


# start comms client on separate thread
t = threading.Thread(target=comms_thread)
t.start()

try:
    asyncio.run(client.connect())
except KeyboardInterrupt:
    pass
finally:
    comms.close()
    client.close()
    controller.stop()
