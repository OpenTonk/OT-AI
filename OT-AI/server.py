import streaming
import cv2
import linedetection
from streaming import AsyncServer
import asyncio
from tankcontrol import TankControl
import json
import comms
import threading

import sys, getopt


ip = "127.0.0.1"
port = 8084
usePiCam = False
saveTrainingData = False


try:
    opts, args = getopt.getopt(sys.argv[1:], "ha:p:s:", ["ip=", "port=", "size=", "usepicam"])
except getopt.GetoptError:
    print("ERROR: server.py -a <server ip> -p <port> -s <size> (--usepicam)")
    exit()

for opt, arg in opts:
    if opt == '-h':
        print("server.py -a <server ip> -p <port> -s <size> (--usepicam --save)")
        exit()
    elif opt in ("-a", "--ip"):
        ip = arg
    elif opt in ("-p", "--port"):
        port = int(arg)
    elif opt == '--usepicam':
        usePiCam = True
    elif opt == '--save':
        saveTrainingData = True


cv2.namedWindow('frame')
cv2.startWindowThread()

server = AsyncServer(ip, port, usePiCam)

comms = comms.AsyncServer(ip, port + 1)

@server.on_frame()
def frame_handler(frame):
    lanes = linedetection.detect_lane(frame)
    steer = linedetection.stabilize_steering_angle(linedetection.compute_steering_angle(
        frame, lanes), linedetection.lastSteerAngle, len(lanes))

    #await comms.send_msg(json.dumps({"angle": steer}))

    if saveTrainingData:
        path = "images/%05d_%03d.png" % (server.frameNum, steer)
        print(path)
        result = cv2.imwrite(path, frame)
        print(result)

    frame = linedetection.display_lines(frame, lanes)
    frame = linedetection.display_heading_line(frame, steer)

    cv2.imshow('frame', frame)
    cv2.waitKey(1)


@comms.on_msg()
async def on_msg(msg):
    print(msg)


def comms_thread():
    asyncio.run(comms.serve())


# start comms client on separate thread
t = threading.Thread(target=comms_thread)
t.start()

asyncio.run(server.serve())
