class TankControl:
    def __init__(self, right: tuple, left: tuple):
        self.right = right
        self.left = left

        self.rightSpeed = 0
        self.leftSpeed = 0

    def drive(self, speed: int, angle: int):
        print(speed, angle)
        if angle > 90:
            self.setRightSpeed((1 - ((angle - 90) / 90)) * speed)
            self.setLeftSpeed((speed))
            return

        if angle < 90:
            self.setLeftSpeed((1 - (angle / 90)) * speed)
            self.setRightSpeed(speed)
            return

        self.setLeftSpeed(speed)
        self.setRightSpeed(speed)

    def setRightSpeed(self, speed: int):
        self.rightSpeed = speed

    def setLeftSpeed(self, speed: int):
        self.leftSpeed = speed
