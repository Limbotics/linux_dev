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
import threading
from collections import Counter

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
        self.cam_data = ""
        self.object_spotted = False
        self.test_count = 0
        self.killed_thread = False
        self.cam_image = None
        self.cam_image_index = 0
        self.object_spotted_T0 = time.time()
        self.object_not_spotted_delta_req = 2

    def camera_read_threader(self):
        #Start the read cam thread
        read_cam = threading.Thread(target=self.read_cam_thread, args=())
        read_cam.start()
        while(self.cam_image_index == 0):
            time.sleep(0.05)
        #Start the image decode thread
        decoder = threading.Thread(target=self.decode_image_thread, args=())
        decoder.start()
        while not self.killed_thread and read_cam.is_alive() and decoder.is_alive():
            time.sleep(0.25)
        #Flag is thrown or error, so ensure flag is thrown and wait for threads to join
        self.killed_thread = True
        read_cam.join()
        decoder.join()

    def decode_image_thread(self):
        previous_index = None
        while not self.killed_thread:
            #Detect and decode the stored image if it's ready
            # t = time.time()
            if(previous_index != self.cam_image_index):
                previous_index = self.cam_image_index
                data, _, _ = self.detector.detectAndDecode(self.cam_image)
                #Define a parameter we can easily read later if anything is detected
                is_object = False
                #Update parameter/output the data we found, if any
                if data:
                    #print("data found: ", data)
                    is_object = True
                #Poll averaging method (possibly deprecated)
                # self.spot_history.insert(0, data)
                # if(len(self.spot_history) > 6):
                #     self.spot_history.pop()
                # self.cam_data = self.Most_Common(self.spot_history)

                #If the camera sees an object, skip the time requirement
                if(data != ""):
                    self.cam_data = data
                    self.object_spotted_T0 = time.time()
                #If the camera doesn't see an object, require a delay before reporting nothing
                else:
                    if((time.time() - self.object_spotted_T0) > self.object_not_spotted_delta_req):
                        self.cam_data = data
                self.object_spotted = is_object
                
                #####No sleep since detecting/decoding takes significant time, just do it as fast as possible
            # print("Time to decode image: " + (str(time.time() - t)))

    def Most_Common(self, lst):
        data = Counter(lst)
        return data.most_common(1)[0][0]

    def read_cam_thread(self):
        while not self.killed_thread:
            #Get camera image, rescale, and store in class variable
            self.cam_image = self.rescale_image(*self.cap.read())
            #Increase index by 1
            self.cam_image_index += 1
            #Pause temply
            time.sleep(0.05)

    def rescale_image(self, _, img):
        # t = time.time()
        scale_percent = 65 # percent of original size
        width = int(img.shape[1] * scale_percent / 100)
        height = int(img.shape[0] * scale_percent / 100)
        dim = (width, height)

        # resize image
        resized = cv2.resize(img, dim, interpolation = cv2.INTER_AREA)
        # print("Time to rescale: " + str(time.time() - t))
        return resized

    def read_cam(self):
        # get the image
        _, img = self.cap.read() #TODO: #14 Downscale the resolution for faster processing
        # get bounding box coords and data
        data, bbox, _ = self.detector.detectAndDecode(img)
        #Define a parameter we can easily read later if anything is detected
        is_object = False
        #Update parameter/output the data we found, if any
        if data:
            #print("data found: ", data)
            is_object = True
        #return the information we got from the camera
        # cv2.imwrite("frame1.jpg", img)     # save frame as JPEG file
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
        cv2.imwrite("frame1.jpg", img)     # save frame as JPEG file
        #self.count += 1

    def end_camera_session(self):
        #Stop the camera thread 
        self.killed_thread = True
        time.sleep(0.1)
        #Release the camera object
        self.cap.release()
        #Destroy all displayed windows
        cv2.destroyAllWindows()
