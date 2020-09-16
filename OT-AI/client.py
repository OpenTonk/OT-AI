import cv2
import numpy as np
import socket
import sys
import pickle
import struct

cap = cv2.VideoCapture('video.mp4')
clientsocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
clientsocket.connect(('127.0.0.1', 8084))

while True:
    ret,frame = cap.read()
    if ret:
        data = pickle.dumps(frame)
        clientsocket.sendall(struct.pack("L", len(data)) + data)
    