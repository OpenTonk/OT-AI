import streaming
import cv2
import linedetection
from streaming import AsyncServer
import asyncio
from tankcontrol import TankControl
import json
import comms
import threading

#cv2.namedWindow('frame')
cv2.startWindowThread()

writer = None

server = AsyncServer('127.0.0.1', 8084)
controller = TankControl((1, 1), (2, 2))

comms = comms.AsyncServer('127.0.0.1', 8085)

@server.on_frame()
async def frame_handler(frame, writer):
    lanes = linedetection.detect_lane(frame)
    steer = linedetection.stabilize_steering_angle(linedetection.compute_steering_angle(
        frame, lanes), linedetection.lastSteerAngle, len(lanes))

    await comms.send_msg(json.dumps({"angle": steer}))

    controller.drive(50, steer)
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
