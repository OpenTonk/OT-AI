import cv2
import linedetection
from streaming import AsyncServer
import asyncio
import comms
import threading
import numpy as np
from keras.models import load_model

import sys
import getopt


ip = "127.0.0.1"
port = 8084
usePiCam = False
saveTrainingData = False
record = False
useML = False


try:
    opts, args = getopt.getopt(sys.argv[1:], "ha:p:s:", [
                               "ip=", "port=", "size=", "usepicam", "save", "record", "useml"])
except getopt.GetoptError:
    print("ERROR: server.py -a <server ip> -p <port> (--usepicam --save --record --useml)")
    exit()

for opt, arg in opts:
    if opt == '-h':
        print("server.py -a <server ip> -p <port> (--usepicam --save --record)")
        exit()
    elif opt in ("-a", "--ip"):
        ip = arg
    elif opt in ("-p", "--port"):
        port = int(arg)
    elif opt == '--usepicam':
        usePiCam = True
    elif opt == '--save':
        saveTrainingData = True
    elif opt == '--record':
        record = True
    elif opt == '--useml':
        useML = True


cv2.namedWindow('frame')

# aanmaken van TCP socket servers
videoServer = AsyncServer(ip, port, usePiCam) # TCP socket server voor ontvangen van beelden
instructionServer = comms.AsyncServer(ip, port + 1) # TCP socket server voor ontvangen en verzenden van instructie's


out = None
if record:
    out = cv2.VideoWriter('output.avi', cv2.VideoWriter_fourcc(
        'M', 'J', 'P', 'G'), 24, (360, 270))

tc = None


if useML:
    model = load_model('./model/lane_navigation.h5')

    def img_preprocess(image):
        height, _, _ = image.shape
        image = image[int(height/2):, :, :]  # remove top half of the image, as it is not relevant for lane following
        image = cv2.cvtColor(image, cv2.COLOR_RGB2YUV)  # Nvidia model said it is best to use YUV color space
        image = cv2.GaussianBlur(image, (3, 3), 0)
        image = cv2.resize(image, (200, 66))  # input image size (200,66) Nvidia model
        image = image / 255  # normalizing
        return image

    def compute_steering_angle(frame):
        preprocessed = img_preprocess(frame)
        X = np.asarray([preprocessed])
        steering_angle = model.predict(X)[0]
        return steering_angle


def on_val(val):
    return


#cv2.createTrackbar("lower H", "frame", 60, 255, on_val)
#cv2.createTrackbar("lower S", "frame", 40, 255, on_val)
#cv2.createTrackbar("lower V", "frame", 40, 255, on_val)

#cv2.createTrackbar("upper H", "frame", 150, 255, on_val)
#cv2.createTrackbar("upper S", "frame", 255, 255, on_val)
#cv2.createTrackbar("upper V", "frame", 255, 255, on_val)

## blue electric tape
cv2.createTrackbar("lower H", "frame", 80, 255, on_val)
cv2.createTrackbar("lower S", "frame", 255, 255, on_val)
cv2.createTrackbar("lower V", "frame", 80, 255, on_val)

cv2.createTrackbar("upper H", "frame", 150, 255, on_val)
cv2.createTrackbar("upper S", "frame", 255, 255, on_val)
cv2.createTrackbar("upper V", "frame", 150, 255, on_val)

cv2.createTrackbar("offset", "frame", 10, 20, on_val)
cv2.createTrackbar("speed", "frame", 0, 100, on_val)


def get_lower():
    return np.array([
        cv2.getTrackbarPos("lower H", "frame"),
        cv2.getTrackbarPos("lower S", "frame"),
        cv2.getTrackbarPos("lower V", "frame")])


def get_upper():
    return np.array([
        cv2.getTrackbarPos("upper H", "frame"),
        cv2.getTrackbarPos("upper S", "frame"),
        cv2.getTrackbarPos("upper V", "frame")])


@videoServer.on_frame()
def frame_handler(frame):
    global record, out
    frameToSave = frame

    if useML:
        steer = compute_steering_angle(frame)
        instructionServer.send_msg({"angle": int((190 / 180) * steer),
                            "speed": cv2.getTrackbarPos("speed", "frame")})
        frame = linedetection.display_heading_line(frame, steer)
    else:
        linedetection.upper_blue = get_upper()
        linedetection.lower_blue = get_lower()
        linedetection.camera_mid_offset_percent = (
            cv2.getTrackbarPos('offset', 'frame') - 10) * 0.01

        lanes = linedetection.detect_lane(frame)
        steer = linedetection.stabilize_steering_angle(
            linedetection.compute_steering_angle(frame, lanes),
            linedetection.lastSteerAngle,
            len(lanes))

        frame = linedetection.display_lines(frame, lanes)
        frame = linedetection.display_heading_line(frame, steer)

        

        if len(lanes) == 0:
            instructionServer.send_msg({"angle": 90, "speed": 0})
        else:
            instructionServer.send_msg({"angle": steer,
                            "speed": cv2.getTrackbarPos("speed", "frame")})
            
            if saveTrainingData and cv2.getTrackbarPos("speed", "frame") > 0:
                path = "images/%05d_%03d.png" % (videoServer.frameNum, steer)
                print(path)
                result = cv2.imwrite(path, frameToSave)
                print(result)

    if record:
        out.write(frame)

    cv2.imshow('frame', frame)
    cv2.waitKey(1)


@videoServer.on_disconnect()
def on_disconnect():
    instructionServer.stop()


@instructionServer.on_msg()
async def on_msg(msg):
    print(msg)


def comms_thread():
    try:
        asyncio.run(instructionServer.serve())
    except KeyboardInterrupt:
        pass
    finally:
        instructionServer.stop()


# start comms client on separate thread
t = threading.Thread(target=comms_thread)
t.start()

try:
    asyncio.run(videoServer.serve())
except KeyboardInterrupt:
    pass
finally:
    videoServer.socket.close()
    instructionServer.socket.close()
    if record:
        out.release()
        cv2.destroyAllWindows()
