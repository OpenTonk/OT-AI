import RPi.GPIO as IO

IO.setwarnings(False)
IO.setmode(IO.BOARD)


class TankControl:
    def __init__(self, right: tuple, left: tuple):
        # setup motorpins
        IO.setup(right[0], IO.OUT)
        IO.setup(right[1], IO.OUT)
        IO.setup(left[0], IO.OUT)
        IO.setup(left[1], IO.OUT)

        # get pwm instances
        self.right = (
            IO.PWM(right[0], 100),
            IO.PWM(right[1], 100)
        )
        self.left = (
            IO.PWM(left[0], 100),
            IO.PWM(left[1], 100)
        )

        self.rightSpeed = 0
        self.leftSpeed = 0

        # start the pwm instances
        self.right[0].start(0)
        self.right[1].start(0)
        self.left[0].start(0)
        self.left[1].start(0)

    def drive(self, speed: int, angle: int):
        if speed == 0:
            self.stop()
            return

        if angle > 90:
            #self.setRightSpeed((1 - ((angle - 90) / 90)) * speed)
            self.setRightSpeed(int((-2/90) * angle + 3) * speed)
            self.setLeftSpeed((speed))
            return

        if angle < 90:
            #self.setLeftSpeed((angle / 90) * speed)
            self.setLeftSpeed(int((2/90) * angle - 1) * speed)
            self.setRightSpeed(speed)
            return

        self.setLeftSpeed(speed)
        self.setRightSpeed(speed)

    def setRightSpeed(self, speed: int):
        self.rightSpeed = speed

        #print("right", speed)

        if speed > 0:
            self.right[0].ChangeDutyCycle(speed)
            self.right[1].ChangeDutyCycle(0)
        elif speed == 0:
            self.right[0].ChangeDutyCycle(0)
            self.right[1].ChangeDutyCycle(0)
        else:
            self.right[0].ChangeDutyCycle(0)
            self.right[1].ChangeDutyCycle(abs(speed))

    def setLeftSpeed(self, speed: int):
        self.leftSpeed = speed

        #print("left", speed)

        if speed > 0:
            self.left[0].ChangeDutyCycle(speed)
            self.left[1].ChangeDutyCycle(0)
        elif speed == 0:
            self.left[0].ChangeDutyCycle(0)
            self.left[1].ChangeDutyCycle(0)
        else:
            self.left[0].ChangeDutyCycle(0)
            self.left[1].ChangeDutyCycle(abs(speed))

    def stop(self):
        self.left[0].ChangeDutyCycle(0)
        self.left[1].ChangeDutyCycle(0)
        self.right[0].ChangeDutyCycle(0)
        self.right[1].ChangeDutyCycle(0)
