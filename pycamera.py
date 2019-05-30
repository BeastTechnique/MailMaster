import picamera
from time import sleep


def take_pic():
    print("About to take a picture")

    with picamera.PiCamera() as camera:
        i = 0
        sleep(.2)
        while i < 10:
            sleep(.1)
            camera.resolution = (1280, 720)
            camera.capture("/home/pi/Documents/cse408/images/{x}.jpg".format(x=i))
            i += 1
            print("Picture " + '#'+ str(i))
    print("Picture Taken")
