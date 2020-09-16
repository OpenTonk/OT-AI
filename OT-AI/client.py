import cv2
import numpy as np
import socket
import sys
import pickle
import struct

#cap = cv2.VideoCapture('video.mp4')
cap = cv2.VideoCapture(0)
clientsocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
clientsocket.connect(('127.0.0.1', 8084))

while True:
    ret,frame = cap.read()
    
    if ret:
        h, w, _ = frame.shape
        frame = cv2.resize(frame, (int(w / 2), int(h / 2)))
        data = pickle.dumps(frame)
        clientsocket.sendall(struct.pack("L", len(data)) + data)
        cv2.waitKey(1)
    