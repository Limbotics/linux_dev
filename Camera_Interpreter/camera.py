#LINUX OPENCV INstall instructions:
# Use -> sudo apt install python3-opencv  
# First, and if that fails, then follow this tutorial
# https://medium.com/@balaji_85683/installing-opencv-4-0-on-google-coral-dev-board-5c3a69d7f52f

# import the necessary packages
from numpy.lib.financial import _convert_when
from imutils.video import VideoStream
from imutils.video import FPS
import numpy as np
import imutils
import math
from PIL import Image
import time
import cv2
# import matplotlib.pyplot as plt
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


from pycoral.adapters.common import input_size
from pycoral.adapters.detect import get_objects
from pycoral.utils.dataset import read_label_file
from pycoral.utils.edgetpu import make_interpreter
from pycoral.utils.edgetpu import run_inference
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
    """

    def __init__(self,live_camera_feed, resolution=(640,480),framerate=30):
        #Try to detect the coral dev board
        if not self.detectCoralDevBoard():
            raise Exception("Dev board not detected.")
        self.count = 0
        self.cap = cv2.VideoCapture(1)
        self.live_camera_feed = live_camera_feed
        print("[INFO] Created video capture object")

        print("[INFO] loading model...")
        #Load the tflite model and labelmap
        # Get path to current working directory
        if False:
            print("[MODEL] Loading 20% MAP model...")
            self.min_conf_threshold = 0.2
            GRAPH_NAME = "mobilenet_ssd_v2_coco_quant_postprocess_edgetpu.tflite"
            MODEL_NAME = "Camera_Interpreter/Coco"
            LABELMAP_NAME = "coco_labels.txt"
            CWD_PATH = os.getcwd()
            # Load the Tensorflow Lite model.
            # If using Edge TPU, use special load_delegate argument
            # Initialize the TF interpreter
            self.interpreter = make_interpreter(os.path.join("/home/mendel/linux_dev", 'Camera_Interpreter/Coco/mobilenet_ssd_v2_coco_quant_postprocess_edgetpu.tflite'))
            self.interpreter.allocate_tensors()
        else:
            print("[MODEL] Loading 40% MAP model...")
            self.min_conf_threshold = 0.4
            GRAPH_NAME = "efficientdet_lite3_512_ptq_edgetpu.tflite"
            MODEL_NAME = "Camera_Interpreter/Edge_TPU_Model"
            LABELMAP_NAME = "coco_labels_efficientdet.txt"
            CWD_PATH = os.getcwd()
            # Load the Tensorflow Lite model.
            # If using Edge TPU, use special load_delegate argument
            # Initialize the TF interpreter
            self.interpreter = make_interpreter(os.path.join("/home/mendel/linux_dev", 'Camera_Interpreter/Edge_TPU_Model/efficientdet_lite3_512_ptq_edgetpu.tflite'))
            self.interpreter.allocate_tensors()

        # Path to .tflite file, which contains the model that is used for object detection
        PATH_TO_CKPT = os.path.join(CWD_PATH,MODEL_NAME,GRAPH_NAME)

        # Path to label map file
        PATH_TO_LABELS = os.path.join(CWD_PATH,MODEL_NAME,LABELMAP_NAME)
        #self.labels = dataset.read_label_file(PATH_TO_LABELS)
        self.labels = read_label_file(PATH_TO_LABELS)

        # Get model details
        self.input_details = self.interpreter.get_input_details()
        self.output_details = self.interpreter.get_output_details()
        self.inference_size = input_size(self.interpreter)
        self.size = input_size(self.interpreter)

        self.floating_model = (self.input_details[0]['dtype'] == np.float32)

        self.input_mean = 127.5
        self.input_std = 127.5
        
        # QR code detection object
        self.cam_data = ""
        self.other_cam_data = []
        self.cam_data_score = 0
        self.inference_time = 1
        self.object_spotted = False
        self.test_count = 0
        self.killed_thread = False
        self.cam_image = None
        self.cam_image_index = 0
        self.object_spotted_T0 = 0
        self.object_not_spotted_delta_req = 5
        self.new_object_spotted_timer = 0.1
        self.centered_line_length_limit = 0

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
                if((data != "" and (time.time() - self.object_spotted_T0) > self.new_object_spotted_timer) or data == self.cam_data):
                    self.cam_data = data
                    self.cam_data_score = score
                    self.object_spotted_T0 = time.time()
                    self.object_spotted = True
                #If the camera doesn't see an object, require a delay before reporting nothing
                else:
                    if((time.time() - self.object_spotted_T0) > self.object_not_spotted_delta_req):
                        # print("[DEBUG] Delta Req passed; reporting no object now")
                        self.cam_data = ""
                        self.cam_data_score = 0
                        self.object_spotted = False
                        self.object_spotted_T0 = time.time()
                
                #####No sleep since detecting/decoding takes significant time, just do it as fast as possible
            # print("[INFO] Time to decode image: " + (str(time.time() - t)))
            
    def detect_main_object(self, frame1):
        # Perform the actual detection by running the model with the image as input
        t = time.time()
        cv2_im_rgb = cv2.cvtColor(frame1, cv2.COLOR_BGR2RGB)
        cv2_im_rgb = cv2.resize(cv2_im_rgb, self.size)
        run_inference(self.interpreter, cv2_im_rgb.tobytes())
        objs = get_objects(self.interpreter, self.min_conf_threshold)

        #Get information about the image
        #More image information
        height, width, channels = cv2_im_rgb.shape
        centered_line_length_limit = int(width/4)

        scale_x, scale_y = width / self.inference_size[0], height / self.inference_size[1]
        #The bounding limits for detecting objects
        min_x = int(width/4)
        max_x = int(width/2)+min_x
        min_y = int(width/4)

        #Determine the midpoint of the detection region
        midpoint_x = int((max_x-min_x)/2) + min_x
        midpoint_y = int((height - min_y)/2) + min_y
        if self.live_camera_feed:
            cv2_im_rgb = cv2.putText(cv2_im_rgb, "M", (midpoint_x, midpoint_y),
                                cv2.FONT_HERSHEY_SIMPLEX, 0.5, (230, 131, 37), 2)
            #Draw the spot region
            # cv2_im_rgb = cv2.circle(cv2_im_rgb, (midpoint_x, midpoint_y), centered_line_length_limit, (0,255,255), 2)
            cv2_im_rgb = cv2.rectangle(cv2_im_rgb, (min_x, min_y), (max_x, height), (0, 255, 0), 2)

        #Information about the highest scoring/closest object
        highest_scoring_label = ""
        highest_score = 0
        min_dist = width
        
        self.other_cam_data = []
        flag = False
        for c in objs:
            flag = True
            object_name = self.labels.get(c.id, c.id)# Look up object name from "labels" array using class index

            #get the bounding box information
            bbox = c.bbox.scale(scale_x, scale_y)
            x0, y0 = int(bbox.xmin), int(bbox.ymin)
            x1, y1 = int(bbox.xmax), int(bbox.ymax)
            bbox_mdpt_x = int((x1-x0)/2)+x0
            bbox_mdpt_y = int((y1-y0)/2)+y0

            # #Put the bounding box on the image
            line_length = int(self.line_length(bbox_mdpt_x, midpoint_x, bbox_mdpt_y, midpoint_y))
            
            pass_dist_test = False
            if bbox_mdpt_x > min_x and bbox_mdpt_x < max_x and bbox_mdpt_y > min_y:
                pass_dist_test = True
            
            was_selected =False
            if((c.score > self.min_conf_threshold) and (c.score <= 1) and pass_dist_test and line_length < min_dist and (object_name in grips.object_to_grip_mapping.value.keys())):
                # Draw label
                was_selected = True
                highest_scoring_label = object_name
                highest_score = c.score
                min_dist = line_length
                # print("[DETECT - INFO] Highest scoring pair: ", highest_scoring_label, ", ", str(highest_score))
            elif (object_name in grips.object_to_grip_mapping.value.keys()) or (c.score > self.min_conf_threshold):
                self.other_cam_data.append((object_name, c.score))

            if self.live_camera_feed:
                color = (0, 0, 255)
                if was_selected:
                    color = (0, 255, 0)
                cv2_im_rgb = cv2.rectangle(cv2_im_rgb, (x0, y0), (x1, y1), color, 2)
                
                #Draw the line from the center of the bounding box to the center of the image
                cv2_im_rgb = cv2.line(cv2_im_rgb, (bbox_mdpt_x,bbox_mdpt_y), (midpoint_x,midpoint_y), color, 5)
                #Draw the text label for the line distance
                cv2_im_rgb = cv2.putText(cv2_im_rgb, object_name, (x0, y0+5),
                                 cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255,255,255), 2)

        #Save the modified image for debugging
        if flag:
            cv2.imwrite("dist_img.jpg", cv2_im_rgb)
        if self.live_camera_feed:
            # cv2_im_rgb = cv2.cvtColor(frame1, cv2.COLOR_RGB2BGR)
            self.im_show(cv2_im_rgb, 'frame')
        self.inference_time = time.time() - t
        return(highest_scoring_label, highest_score)

    def im_show(self, img, name):

        cv2.namedWindow(name)
        cv2.moveWindow(name, 900,-900)
        cv2.namedWindow(name, cv2.WINDOW_AUTOSIZE)
        # cv2.setWindowProperty("window",cv2.WND_PROP_FULLSCREEN,cv2.WINDOW_AUTOSIZE)
        cv2.imshow(name, img)
        cv2.waitKey(1)
        return

    def line_length(self, x0, x1, y0, y1):
        return math.sqrt(((x1-x0)**2) + (y1-y0)**2)

    def read_cam_thread(self):
        while not self.killed_thread:
            time.sleep(0.01)
            if(not self.temp_pause): #CAMBUG remove False
                _, self.cam_image = self.cap.read()

                #Increase index by 1
                self.cam_image_index += 1

    def end_camera_session(self):
        print("[CAM] Attempting to end camera session...")
        #Stop the camera thread 
        self.killed_thread = True
        #Release the camera object
        self.cap.release()
        if self.live_camera_feed:
            cv2.destroyAllWindows()
        print("[CAM] Successfully killed camera session.")

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