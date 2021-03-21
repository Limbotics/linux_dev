from adafruit_servokit import ServoKit


class handServoControl:

    def __init__(self):

        #this class is the lookup table servo control because the functions kind of do everything already 
        #16 channel piHat
        self.kit = ServoKit(channels=16)

    #0 - Thumb
    #1 - Index
    #2 - Middle
    #3 - Ring
    #4 - Pinky

    def moveThumb(self, angle):
        self.kit.servo[0].angle = angle

    def moveIndex(self, angle):
        self.kit.servo[1].angle = angle

    def moveMiddle(self, angle):
        self.kit.servo[2].angle = angle

    def moveRing(self, angle):
        self.kit.servo[3].angle = angle

    def movePinky(self, angle):
        self.kit.servo[4].angle = angle


#https://www.w3schools.com/python/python_inheritance.asp

#this child class is the look up table and needs the most real world tuning
class handLUTControl(handServoControl):
    def __init__(self, grip_config="openHand"):
        super().__init__()
        self.grip_config = grip_config

    def openGrip(self):
        self.moveThumb(0)
        self.moveIndex(0)
        self.moveMiddle(0)
        self.moveRing(0)
        self.movePinky(0)
    
    def closeGrip(self):
        self.moveThumb(180)
        self.moveIndex(180)
        self.moveMiddle(180)
        self.moveRing(180)
        self.movePinky(180)

    def pencilGrip(self):
        self.moveThumb(150)
        self.moveIndex(120)
        self.moveMiddle(180)
        self.moveRing(180)
        self.movePinky(180)

    def cupGrip(self):
        self.moveThumb(140)
        self.moveIndex(160)
        self.moveMiddle(160)
        self.moveRing(160)
        self.movePinky(160)

    def loopHandLUTControl(self):

        if self.grip_config == "openHand":
            self.openGrip()

        if self.grip_config == "closeHand":
            self.closeGrip()

        if self.grip_config == "pencil":
            self.pencilGrip()
        
        if self.grip_config == "cup":
            self.cupGrip()