import streaming
import cv2
import linedetection

server = streaming.Server(('192.168.111.106', 8084))

cv2.namedWindow('frame')
cv2.startWindowThread()

steer = 0

while True:
    server.wait_for_connection()
    print("client connected")

    while True:
        frame = server.get_frame()

        if type(frame) == bool:
            break
        
        lanes = linedetection.detect_lane(frame)
        steer = linedetection.stabilize_steering_angle(linedetection.compute_steering_angle(frame, lanes), steer, len(lanes))
        frame = linedetection.display_lines(frame, lanes)
        frame = linedetection.display_heading_line(frame, steer)
        cv2.imshow('frame', frame)
        cv2.waitKey(1)

    print("client disconnected")
    #cv2.destroyAllWindows()
    
