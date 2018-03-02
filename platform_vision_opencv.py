from __future__ import print_function
from imutils.video.pivideostream import PiVideoStream
from imutils.video import FPS
from collections import deque
from picamera.array import PiRGBArray
from picamera import PiCamera
import logging
import time
import numpy as np
import argparse
import imutils
import cv2
import threading
import math
from websocket import create_connection 
import asyncio


# initialize the camera and grab a reference to the raw camera capture
camera = PiCamera()
camera.resolution = (640, 480)
camera.framerate = 64
rawCapture = PiRGBArray(camera, size=(640, 480))
stream = camera.capture_continuous(rawCapture, format="bgr",
    use_video_port=True)

# define the lower and upper boundaries of the "green"
# ball in the HSV color space
greenLower = (29, 86, 6)
greenUpper = (64, 255, 255)

# initialize the list of tracked points, the frame counter,
# and the coordinate deltas
pts = deque(maxlen=32)
counter = 0
(dX, dY) = (0, 0)
direction = ""
xPast = 0
yPast = 0 
xDelta = 0
yDelta = 0 
xCurrent = 0
motorSteer = ""
camSteer = ""

time.sleep(2.0)
fps = FPS().start()

# stop the timer and display FPS information
fps.stop()
print("[INFO] elasped time: {:.2f}".format(fps.elapsed()))
print("[INFO] approx. FPS: {:.2f}".format(fps.fps()))

# do a bit of cleanup
cv2.destroyAllWindows()
stream.close()
rawCapture.close()
camera.close()

# created a *threaded *video stream, allow the camera sensor to warmup,
# and start the FPS counter
print("[INFO] sampling THREADED frames from `picamera` module...")
vs = PiVideoStream().start()
time.sleep(2.0)
fps = FPS().start()
#ws = create_connection('ws://192.168.178.61:8080/')


# capture frames from the camera
while True:
    # grab the raw NumPy array representing the image, then initialize the timestamp
    # and occupied/unoccupied text
  
    frame = vs.read()
    frame = imutils.resize(frame, width=650, height=480)
    # blurred = cv2.GaussianBlur(frame, (11, 11), 0)
    hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)

    # construct a mask for the color "green", then perform
    # a series of dilations and erosions to remove any small
    # blobs left in the mask
    mask = cv2.inRange(hsv, greenLower, greenUpper)
    mask = cv2.erode(mask, None, iterations=3)
    mask = cv2.dilate(mask, None, iterations=3)

    # find contours in the mask and initialize the current
    # (x, y) center of the ball
    cnts = cv2.findContours(mask.copy(), cv2.RETR_EXTERNAL,
            cv2.CHAIN_APPROX_SIMPLE)[-2]
    center = None
    # only proceed if at least one contour was found
    if len(cnts) > 0:
            # find the largest contour in the mask, then use
            # it to compute the minimum enclosing circle and
            # centroid
            c = max(cnts, key=cv2.contourArea)
            ((x, y), radius) = cv2.minEnclosingCircle(c)
            M = cv2.moments(c)
            center = (int(M["m10"] / M["m00"]), int(M["m01"] / M["m00"]))

            # only proceed if the radius meets a minimum size
            if radius > 10:
                    # draw the circle and centroid on the frame,
                    # then update the list of tracked points
                    if x != xPast:
                        xDelta = np.abs(x - xPast)
                        xPast = x
                        
                    if y != yPast:
                        yDelta = np.abs(y - yPast)
                        yPast = y
                        
                    cv2.circle(frame, (int(x), int(y)), int(radius),
                            (0, 255, 255), 2)
                    cv2.circle(frame, center, 5, (0, 0, 255), -1)
                    pts.appendleft(center)

    # loop over the set of tracked points
    for i in np.arange(1, len(pts)):
            # if either of the tracked points are None, ignore
            # them
            if pts[i - 1] is None or pts[i] is None:
                    continue

            # check to see if enough points have been accumulated in
            # the buffer
            if counter >= 10 and i == 1 and pts[-10] is not None:
                    # compute the difference between the x and y
                    # coordinates and re-initialize the direction
                    # text variables
                    dX = pts[-10][0] - pts[i][0]
                    dY = pts[-10][1] - pts[i][1]
                    (dirX, dirY) = ("", "")
                    ws = create_connection('ws://192.168.178.61:8080/')                    

                    # ensure there is significant movement in the
                    # x-direction
                    if np.abs(dX) > 20:
                            dirX = "East" if np.sign(dX) == 1 else "West"

                    # ensure there is significant movement in the
                    # y-direction
                    if np.abs(dY) > 20:
                            dirY = "North" if np.sign(dY) == 1 else "South"

                    # handle when both directions are non-empty
                    if dirX != "" and dirY != "":
                            direction = "{}-{}".format(dirY, dirX)

                    # otherwise, only one direction is non-empty
                    else:
                            direction = dirX if dirX != "" else dirY
                    # ensure there is significant movement in the
                    # y-direction

                    ws = create_connection('ws://192.168.178.67:8080/')
                    ws.send(str(x)+","+str(y))
                    ws.close()



                    if x > 260 and x < 340:
                        if motorSteer == "left" or motorSteer == "right":
                            motorSteer = ""
                            ws = create_connection('ws://192.168.178.61:8080/')
                            ws.send("stop,1.0")
                            ws.close()
                    

                    if x < 260 and xDelta != 0:
                        if motorSteer == "right" or motorSteer == "" or motorSteer == "left" and dX > 12:
                            motorSteer = "left"
                            temp = 0
                            ws = create_connection('ws://192.168.178.61:8080/')
                            if math.fabs(dX/100) > 1.45:
                                dX = 145
                            if math.fabs(dX/100) < 1.0:
                                dX = 100
                            ws.send("left"+","+str(math.fabs(dX/100)))
                            ws.close()

                    if x > 340 and xDelta != 0:
                        if motorSteer == "left" or motorSteer == "" or motorSteer == "right" and dX > 12:
                            motorSteer = "right"
                            speed = xDelta * 2.5
                            if xDelta > 255:
                                speed = 255
                            if xDelta < 35:
                                speed = 45    
                            ws = create_connection('ws://192.168.178.61:8080/')
                            ws.send("right"+","+str(math.fabs(speed/100)))
                            ws.close()

                    if radius > 100:
                        if motorSteer == "backward" or motorSteer == "":
                            motorSteer = "forward"
                            #ws = create_connection('ws://192.168.178.66:8080/')
                            #ws.send("forward")
                            #ws.close()


                    if y > 180 and y < 360:
                        if camSteer == "camup" or camSteer == "camdown":
                            camSteer = ""
                            ws = create_connection('ws://192.168.178.66:8080/')
                            ws.send("camstop")
                            ws.close()

                    if y < 180:
                        if camSteer == "camdown" or camSteer == "":
                            camSteer = "camup"
                            ws = create_connection('ws://192.168.178.66:8080/')
                            ws.send("camup")
                            ws.close()

                    if y > 360:
                        if camSteer == "camup" or camSteer == "":
                            camSteer = "camdown"
                            ws = create_connection('ws://192.168.178.66:8080/')
                            ws.send("camdown")
                            ws.close()


                    if radius < 40:
                        if motorSteer == "forward" or motorSteer == "":
                            motorSteer = "backward"
                            ws = create_connection('ws://192.168.178.66:8080/')
                            ws.send("backward")
                            ws.close()

                    if radius > 40 and radius < 100:
                        if motorSteer == "forward" or motorSteer == "backward":
                            motorSteer = ""
                            ws = create_connection('ws://192.168.178.61:8080/')
                            ws.send("stop")
                            ws.close()


    # show the movement deltas and the direction of movement on
    # the frame
    cv2.putText(frame, direction, (10, 30), cv2.FONT_HERSHEY_SIMPLEX,
            0.45, (255, 255, 0), 1)
    cv2.putText(frame, "dx: {}, dy: {}".format(dX, dY),
            (10, frame.shape[0] - 10), cv2.FONT_HERSHEY_SIMPLEX,
            0.35, (255, 255, 0), 1)

    
    cv2.putText(frame, "radius: " + str(radius),
            (10, frame.shape[0] - 30), cv2.FONT_HERSHEY_SIMPLEX,
            0.35, (255, 255, 0), 1)


    cv2.putText(frame, "x: " + str(x),
            (10, frame.shape[0] - 50), cv2.FONT_HERSHEY_SIMPLEX,
            0.35, (255, 255, 0), 1)

    cv2.putText(frame, "y: " + str(y),
            (10, frame.shape[0] - 70), cv2.FONT_HERSHEY_SIMPLEX,
            0.35, (255, 255, 0), 1)

    
    cv2.putText(frame, "deltaX: " + str(xDelta),
            (10, frame.shape[0] - 90), cv2.FONT_HERSHEY_SIMPLEX,
            0.35, (255, 255, 0), 1)

    cv2.putText(frame, "deltaY: " + str(yDelta),
            (10, frame.shape[0] - 110), cv2.FONT_HERSHEY_SIMPLEX,
            0.35, (255, 255, 0), 1)


    if 1 > 0:
            cv2.imshow("Frame", frame)
            key = cv2.waitKey(1) & 0xFF
            counter += 1
            fps.update()

    if counter == 500:
        fps.stop()
        print("[INFO] approx. wooof FPS: {:.2f}".format(fps.fps()))


# cleanup the camera and close any open windows
camera.close()
cv2.destroyAllWindows()
