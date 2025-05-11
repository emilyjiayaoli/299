from xarm import Controller, Servo

arm = Controller('USB')

# Define each servo at neutral position (500)
s1 = Servo(1, 500)
s2 = Servo(2, 500)
s3 = Servo(3, 500)
s4 = Servo(4, 500)
s5 = Servo(5, 500)
s6 = Servo(6, 500)

# Move all at once with a 2 second duration
arm.setPosition([s1, s2, s3, s4, s5, s6], duration=2000, wait=True)