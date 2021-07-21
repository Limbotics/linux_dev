#LINUX OPENCV INstall instructions:
# Use -> sudo apt install python3-opencv  
# First, and if that fails, then follow this tutorial
# https://medium.com/@balaji_85683/installing-opencv-4-0-on-google-coral-dev-board-5c3a69d7f52f

# import the necessary packages
from imutils.video import VideoStream
from imutils.video import FPS
import numpy as np
import imutils
from PIL import Image
import time
import cv2
import matplotlib.pyplot as plt
#import cvlib as cv
import threading
from collections import Counter

# import importlib.util
# pkg = importlib.util.find_spec('tflite_runtime')
# if pkg:
#     from tflite_runtime.interpreter import Interpreter
#     # if use_TPU:
#     #     from tflite_runtime.interpreter import load_delegate
# else:
#     from tensorflow.lite.python.interpreter import Interpreter
#     # if use_TPU:
#     #     from tensorflow.lite.python.interpreter import load_delegate

from pycoral.utils import edgetpu
from pycoral.utils import dataset
from pycoral.adapters import common
from pycoral.adapters import classify

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
#TODO: Implement the following
#https://towardsdatascience.com/object-detection-with-less-than-10-lines-of-code-using-python-2d28eebc5b11



class camera_interface():
    """
    The main interface for using the camera and determining the grip we need to be in.
    https://www.hackster.io/gatoninja236/scan-qr-codes-in-real-time-with-raspberry-pi-a5268b
      
    Attributes:
        count (int): Count of saved screenshots. File titles are frame'count'.jpg.
        cap (cv2 VideoCapture): The VideoCapture object.
        detector (QRCodeDetector): The QR Code detecting object.
    """

    def __init__(self,resolution=(640,480),framerate=30):
        self.count = 0
        self.cap = cv2.VideoCapture(1)
        #self.vs = VideoStream(resolution=(640,480),framerate=30).start() #CAMBUG
        # self.stream = cv2.VideoCapture(0)
        # ret = self.stream.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc(*'MJPG'))
        # ret = self.stream.set(3,resolution[0])
        # ret = self.stream.set(4,resolution[1])

        #Wait for the camera to startup for one seconds
        time.sleep(1)
        print("[INFO] Created video capture object")
        print("[INFO] loading model...")

        #Load the tflite model and labelmap
        # Get path to current working directory
        GRAPH_NAME = "detect.tflite"
        MODEL_NAME = "Camera_Interpreter/Coco"
        LABELMAP_NAME = "labelmap.txt"
        CWD_PATH = os.getcwd()

        # Path to .tflite file, which contains the model that is used for object detection
        PATH_TO_CKPT = os.path.join(CWD_PATH,MODEL_NAME,GRAPH_NAME)

        # Path to label map file
        PATH_TO_LABELS = os.path.join(CWD_PATH,MODEL_NAME,LABELMAP_NAME)
        self.labels = dataset.read_label_file(PATH_TO_LABELS)

        # Load the label map
        #with open(PATH_TO_LABELS, 'r') as f:
        #    self.labels = [line.strip() for line in f.readlines()]

        # Have to do a weird fix for label map if using the COCO "starter model" from
        # https://www.tensorflow.org/lite/models/object_detection/overview
        # First label is '???', which has to be removed.
        #if self.labels[0] == '???':
        #    del(self.labels[0])

        # Load the Tensorflow Lite model.
        # If using Edge TPU, use special load_delegate argument
        # Initialize the TF interpreter
        self.interpreter = edgetpu.make_interpreter(os.path.join("/home/mendel/linux_dev", 'Camera_Interpreter/Coco/detect.tflite'))
        self.interpreter.allocate_tensors()

        # Get model details
        self.input_details = self.interpreter.get_input_details()
        self.output_details = self.interpreter.get_output_details()
        self.height = self.input_details[0]['shape'][1]
        self.width = self.input_details[0]['shape'][2]
        self.size = common.input_size(self.interpreter)

        self.floating_model = (self.input_details[0]['dtype'] == np.float32)

        self.input_mean = 127.5
        self.input_std = 127.5
        
        # QR code detection object
        # self.detector = cv2.QRCodeDetector()
        self.cam_data = ""
        self.object_spotted = False
        self.test_count = 0
        self.killed_thread = False
        self.cam_image = None
        self.cam_image_index = 0
        self.object_spotted_T0 = 0
        self.object_not_spotted_delta_req = 3

        #Initialize the paused flag to false
        self.temp_pause = False

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
            if(previous_index != self.cam_image_index and (not self.temp_pause) and (self.cam_image is not None)):
                previous_index = self.cam_image_index
                # data, _, _ = self.detector.detectAndDecode(self.cam_image) Deprecated QR Code reader
                data, score = self.detect_main_object(self.cam_image)
                # print("[INFO] Camera objects: " + data)
                # if(data not in grips._value2member_map_):
                #     data = grips.openGrip.value

                #If the camera sees an object, skip the time requirement
                if(data != ""):
                    self.cam_data = data
                    self.object_spotted_T0 = time.time()
                    self.object_spotted = True
                #If the camera doesn't see an object, require a delay before reporting nothing
                else:
                    if((time.time() - self.object_spotted_T0) > self.object_not_spotted_delta_req):
                        # print("[DEBUG] Delta Req passed; reporting no object now")
                        self.cam_data = data
                        self.object_spotted = False
                
                #####No sleep since detecting/decoding takes significant time, just do it as fast as possible
            # print("[INFO] Time to decode image: " + (str(time.time() - t)))
            time.sleep(0.01)

    def detect_main_object(self, frame1):
        min_conf_threshold = 0.35

        # Acquire frame and resize to expected shape [1xHxWx3]
        frame = frame1.copy()
        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        frame_resized = cv2.resize(frame_rgb, (self.width, self.height), interpolation = cv2.INTER_AREA)

        print("[RESIZE-DEBUG] New image dimensions: ", str(frame_resized.shape))
        input_data = np.expand_dims(frame_resized, axis=0)

        # Normalize pixel values if using a floating model (i.e. if model is non-quantized)
        if self.floating_model:
            input_data = (np.float32(input_data) - self.input_mean) / self.input_std

        # Perform the actual detection by running the model with the image as input
        t = time.time()
        common.set_input(self.interpreter, frame1)
        self.interpreter.invoke()
        classes = classify.get_classes(self.interpreter, top_k=1)


        # Retrieve detection results
        # boxes = self.interpreter.get_tensor(self.output_details[0]['index'])[0] # Bounding box coordinates of detected objects
        #classes = self.interpreter.get_tensor(self.output_details[1]['index'])[0] # Class index of detected objects
        #scores = self.interpreter.get_tensor(self.output_details[2]['index'])[0] # Confidence of detected objects

        highest_scoring_label = ""
        highest_score = 0
        for c in classes:
            object_name = self.labels.get(c.id, c.id)# Look up object name from "labels" array using class index
            if((c.score > min_conf_threshold) and (c.score <= 1.0) and (c.score > highest_score) and (object_name in grips._value2member_map_)):
                # Draw label
                highest_scoring_label = object_name
                highest_score = c.score
                print("[DETECT - INFO] Highest scoring pair: ", highest_scoring_label, ", ", str(highest_score))
        #return (highest_scoring_label, highest_score)
        print("[TENSOR-INFO] Time to get classifying data from TPU: ", str(time.time() - t), " s.")
        print("[TENSOR-INFO] Approx. ", str(1/(time.time() - t)), " fps")
        return("banana", 10)


    def read_cam_thread(self):
        flag = True #CAMBUG
        while not self.killed_thread:
            #All Cambug
            
            time.sleep(0.2)
            if(not self.temp_pause): #CAMBUG remove False
                # t = time.time()
                #Get camera image, rescale, and store in class variable
                # script_dir = "/home/mendel/linux_dev"
                # size = common.input_size(self.interpreter)
                # image_file = os.path.join(script_dir, 'cell.jpg')
                # print(str(image_file))
                # self.cam_image = Image.open(image_file).convert('RGB').resize(size, Image.ANTIALIAS)
                #frame = self.vs.read() #CAMBUG
                _, img = self.cap.read()
                cv2.imwrite("frame1.jpg", img)
                self.cam_image = imutils.resize(img, width=300)
                flag = False
                
                #Increase index by 1
                self.cam_image_index += 1
                #Pause temply
                time.sleep(0.2)

    # def read_cam(self):
    #     # get the image
    #     _, img = self.cap.read() #TODO: #14 Downscale the resolution for faster processing
    #     # get bounding box coords and data
    #     data, bbox, _ = self.detector.detectAndDecode(img)
    #     #Define a parameter we can easily read later if anything is detected
    #     is_object = False
    #     #Update parameter/output the data we found, if any
    #     if data:
    #         #print("data found: ", data)
    #         is_object = True
    #     #return the information we got from the camera
        # cv2.imwrite("frame1.jpg", img)     # save frame as JPEG file
    #     return data, bbox, img, is_object

    # def read_cam_display_out(self):
    #     #Call the standard method to get the qr data / bounding box
    #     data, bbox, img, _ = self.read_cam()
    #     # if there is a bounding box, draw one, along with the data
    #     if(bbox is not None):
    #         for i in range(len(bbox)):
    #             cv2.line(img, tuple(bbox[i][0]), tuple(bbox[(i+1) % len(bbox)][0]), color=(255,
    #                     0, 255), thickness=2)
    #         cv2.putText(img, data, (int(bbox[0][0][0]), int(bbox[0][0][1]) - 10), cv2.FONT_HERSHEY_SIMPLEX,
    #                     0.5, (0, 255, 0), 2)
    #         #if data:
    #             #print("data found: ", data)
    #     # display the image preview
    #     cv2.imshow("code detector", img)

    #     # save the image
    #     cv2.imwrite("frame1.jpg", img)     # save frame as JPEG file
    #     #self.count += 1

    def end_camera_session(self):
        #Stop the camera thread 
        self.killed_thread = True
        time.sleep(0.1)
        #Release the camera object
        #self.vs.stop() #CAMBUG
        #Destroy all displayed windows
        # cv2.destroyAllWindows()
