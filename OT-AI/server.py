import streaming
import cv2
import linedetection
from streaming import AsyncServer
import asyncio

cv2.namedWindow('frame')
cv2.startWindowThread()

writer = None

server = AsyncServer('127.0.0.1', 8084)


@server.on_frame()
async def frame_handler(frame):
    lanes = linedetection.detect_lane(frame)
    steer = linedetection.stabilize_steering_angle(linedetection.compute_steering_angle(
        frame, lanes), linedetection.lastSteerAngle, len(lanes))
    frame = linedetection.display_lines(frame, lanes)
    frame = linedetection.display_heading_line(frame, steer)

    try:
        writer.write(frame)
    except:
        (h, w) = frame.shape[:2]
        writer = cv2.VideoWriter(
            './output.avi', cv2.VideoWriter_fourcc(*'XVID'), 30, (w, h), True)

    cv2.imshow('frame', frame)
    cv2.waitKey(1)
    writer.release()


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
