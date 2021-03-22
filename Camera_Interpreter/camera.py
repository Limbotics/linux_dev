# import the necessary packages
from imutils.video import VideoStream
from imutils.video import FPS
import numpy as np
import argparse
import imutils
import time
import cv2

from enum import Enum

class states(Enum):
    state_1 = 1
    state_2 = 2

#https://www.pyimagesearch.com/2017/09/18/real-time-object-detection-with-deep-learning-and-opencv/
#https://www.pyimagesearch.com/2017/09/11/object-detection-with-deep-learning-and-opencv/
#https://www.pyimagesearch.com/2019/09/02/opencv-stream-video-to-web-browser-html-page/


class camera_interface():

    def __init__(self):
        my_var = 2

    def get_my_var(self):
        return states.state_1