import streaming
import cv2
import linedetection
from streaming import AsyncServer
import asyncio
from tankcontrol import TankControl
import json

#cv2.namedWindow('frame')
cv2.startWindowThread()

writer = None

server = AsyncServer('192.168.111.106', 8084)
controller = TankControl((1, 1), (2, 2))

@server.on_frame()
async def frame_handler(frame, writer):
    lanes = linedetection.detect_lane(frame)
    steer = linedetection.stabilize_steering_angle(linedetection.compute_steering_angle(
        frame, lanes), linedetection.lastSteerAngle, len(lanes))
    controller.drive(50, steer)
    frame = linedetection.display_lines(frame, lanes)
    frame = linedetection.display_heading_line(frame, steer)

    d = {
        "speed": 40,
        "angle": steer
    }
    server.send_msg(writer, json.dumps(d))
    await writer.drain()

    cv2.imshow('frame', frame)
    cv2.waitKey(1)


asyncio.run(server.serve())


"""
server = streaming.Server(('192.168.111.106', 8084))

while True:
    server.wait_for_connection()
    print("client connected")

    while True:
        frame = server.get_frame()

        if type(frame) == bool:
            break

        lanes = linedetection.detect_lane(frame)
        steer = linedetection.stabilize_steering_angle(
            linedetection.compute_steering_angle(frame, lanes), steer, len(lanes))
        frame = linedetection.display_lines(frame, lanes)
        frame = linedetection.display_heading_line(frame, steer)
        cv2.imshow('frame', frame)
        cv2.waitKey(1)

    print("client disconnected")
    # cv2.destroyAllWindows()
"""
