import streaming
import asyncio
import cv2

server = streaming.Server(('127.0.0.1', 8083))

while True:
    server.wait_for_connection()
    print("client connected")

    while True:
        frame = server.get_frame()

        if frame:
            cv2.imshow('frame', frame)

    print("client disconnected")
    
