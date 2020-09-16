import cv2

cap = cv2.VideoCapture('video.mp4')

while True:
    ret, frame = cap.read()

    print(frame)

    cv2.imshow('frame', frame)
    cv2.waitKey(10)
