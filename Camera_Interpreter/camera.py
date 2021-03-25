# import the necessary packages
from imutils.video import VideoStream
from imutils.video import FPS
import numpy as np
import argparse
import imutils
import time
from picamera.array import PiRGBArray
from picamera import PiCamera
import cv2

import sys
import os
sys.path.append(os.path.abspath('../Hand_Classes')) # Adds higher directory to python modules path.

from enum import Enum

from Hand_Classes import hand_interface
fingers = hand_interface.fingers
grips = hand_interface.grips

#https://www.pyimagesearch.com/2017/09/18/real-time-object-detection-with-deep-learning-and-opencv/
#https://www.pyimagesearch.com/2017/09/11/object-detection-with-deep-learning-and-opencv/
#https://www.pyimagesearch.com/2019/09/02/opencv-stream-video-to-web-browser-html-page/


class camera_interface():
    """
    The main interface for using the camera and determining the grip we need to be in.
    https://www.hackster.io/gatoninja236/scan-qr-codes-in-real-time-with-raspberry-pi-a5268b
      
    Attributes:
        count (int): Count of saved screenshots. File titles are frame'count'.jpg.
        cap (cv2 VideoCapture): The VideoCapture object.
        detector (QRCodeDetector): The QR Code detecting object.
    """
    

    def __init__(self):
        self.count = 0
        self.cap = cv2.VideoCapture(0)
        print("Created video capture object")
        # QR code detection object
        self.detector = cv2.QRCodeDetector()
        
    def read_cam(self):
        # get the image
        _, img = self.cap.read()
        # get bounding box coords and data
        data, bbox, _ = self.detector.detectAndDecode(img)
        #Define a parameter we can easily read later if anything is detected
        is_object = False
        #Update parameter/output the data we found, if any
        if data:
            print("data found: ", data)
            is_object = True
        #return the information we got from the camera
        return data, bbox, img, is_object

    def read_cam_display_out(self):
        #Call the standard method to get the qr data / bounding box
        data, bbox, img, _ = self.read_cam()
        # if there is a bounding box, draw one, along with the data
        if(bbox is not None):
            for i in range(len(bbox)):
                cv2.line(img, tuple(bbox[i][0]), tuple(bbox[(i+1) % len(bbox)][0]), color=(255,
                        0, 255), thickness=2)
            cv2.putText(img, data, (int(bbox[0][0][0]), int(bbox[0][0][1]) - 10), cv2.FONT_HERSHEY_SIMPLEX,
                        0.5, (0, 255, 0), 2)
            #if data:
                #print("data found: ", data)
        # display the image preview
        cv2.imshow("code detector", img)

        # save the image
        #cv2.imwrite("frame%d.jpg" % self.count, img)     # save frame as JPEG file
        #self.count += 1

    def end_camera_session(self):
        #Release the camera object
        self.cap.release()
        #Destroy all displayed windows
        cv2.destroyAllWindows()
