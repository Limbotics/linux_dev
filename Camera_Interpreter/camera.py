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
from pycoral.adapters import detect
from pycoral.adapters import common
from pycoral.adapters import classify
from pycoral.utils.dataset import read_label_file
from pycoral.utils.edgetpu import run_inference
import tflite_runtime.interpreter as tflite

import re

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
        #Try to detect the coral dev board
        if not self.detectCoralDevBoard():
            raise Exception("Dev board not detected.")
        self.count = 0
        self.cap = cv2.VideoCapture(1)

        #Wait for the camera to startup for one seconds
        time.sleep(1)
        print("[INFO] Created video capture object")
        print("[INFO] loading model...")

        #Load the tflite model and labelmap
        # Get path to current working directory
        GRAPH_NAME = "ssd_mobilenet_v1_coco_quant_postprocess_edgetpu.tflite"
        MODEL_NAME = "Camera_Interpreter/Edge_TPU_Model"
        LABELMAP_NAME = "coco_labels.txt"
        CWD_PATH = os.getcwd()

        # Path to .tflite file, which contains the model that is used for object detection
        PATH_TO_CKPT = os.path.join(CWD_PATH,MODEL_NAME,GRAPH_NAME)

        # Path to label map file
        PATH_TO_LABELS = os.path.join(CWD_PATH,MODEL_NAME,LABELMAP_NAME)
        #self.labels = dataset.read_label_file(PATH_TO_LABELS)
        self.labels = read_label_file(PATH_TO_LABELS)

        # Load the Tensorflow Lite model.
        # If using Edge TPU, use special load_delegate argument
        # Initialize the TF interpreter
        #self.interpreter = edgetpu.make_interpreter(os.path.join("/home/mendel/linux_dev", 'Camera_Interpreter/Edge_TPU_Model/ssd_mobilenet_v1_coco_quant_postprocess_edgetpu.tflite'))
        self.interpreter = tflite.Interpreter(os.path.join("/home/mendel/linux_dev", 'Camera_Interpreter/Edge_TPU_Model/ssd_mobilenet_v1_coco_quant_postprocess_edgetpu.tflite'), experimental_delegates=[tflite.load_delegate('libedgetpu.so.1')])
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
        while (not self.killed_thread) and read_cam.is_alive() and decoder.is_alive():
            time.sleep(0.25)
        #Flag is thrown or error, so ensure flag is thrown and wait for threads to join
        self.killed_thread = True

    def decode_image_thread(self):
        previous_index = None
        while not self.killed_thread:
            #Detect and decode the stored image if it's ready
            # t = time.time()
            if(previous_index != self.cam_image_index and (not self.temp_pause) and (self.cam_image is not None)):
                previous_index = self.cam_image_index
                # data, _, _ = self.detector.detectAndDecode(self.cam_image) Deprecated QR Code reader
                data, score = self.detect_main_object(self.cam_image)

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
        min_conf_threshold = 0.4

        # Perform the actual detection by running the model with the image as input
        t = time.time()
        cv2_im_rgb = cv2.cvtColor(frame1, cv2.COLOR_BGR2RGB)
        cv2_im_rgb = cv2.resize(cv2_im_rgb, (self.width, self.height))
        run_inference(self.interpreter, cv2_im_rgb.tobytes())
        objs = detect.get_objects(self.interpreter, min_conf_threshold)

        highest_scoring_label = ""
        highest_score = 0
        for c in objs:
            object_name = self.labels.get(c.id, c.id)# Look up object name from "labels" array using class index
            if((c.score > min_conf_threshold) and (c.score <= 1.0) and (c.score > highest_score) and (object_name in grips._value2member_map_)):
                # Draw label
                highest_scoring_label = object_name
                highest_score = c.score
                print("[DETECT - INFO] Highest scoring pair: ", highest_scoring_label, ", ", str(highest_score))
        #return (highest_scoring_label, highest_score)
        print("[TENSOR-INFO] Time to get classifying data from TPU: ", str(time.time() - t), " s.")
        print("[TENSOR-INFO] Approx. ", str(1/(time.time() - t)), " fps")
        return(highest_scoring_label, highest_score)


    def read_cam_thread(self):
        while not self.killed_thread:
            #time.sleep(0.2)#what is this
            if(not self.temp_pause): #CAMBUG remove False
                _, self.cam_image = self.cap.read()

                #Increase index by 1
                self.cam_image_index += 1

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
        self.cap.release() #CAMBUG
        cv2.destroyAllWindows()

    def load_labels(self, path):
        p = re.compile(r'\s*(\d+)(.+)')
        with open(path, 'r', encoding='utf-8') as f:
            lines = (p.match(line).groups() for line in f.readlines())
            return {int(num): text.strip() for num, text in lines}

    def detectCoralDevBoard(self):
        try:
            if 'MX8MQ' in open('/sys/firmware/devicetree/base/model').read():
                print('Detected Edge TPU dev board.')
            return True
        except: pass
        return False