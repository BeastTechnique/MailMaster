import time
import threading
#camera
import RPi.GPIO as GPIO
import sys
import signal
import pycamera as camera
#fingerprint
import tempfile
import hashlib
from pyfingerprint import PyFingerprint
#firebase
import firebase_admin
from firebase_admin import credentials
from firebase_admin import storage
from firebase_admin import auth
from firebase_admin import db
from time import gmtime, strftime, localtime

cred = credentials.Certificate("/home/pi/Documents/cse408/MailMaster/mailbox-83ab9-firebase-adminsdk-mch9f-c8028acea2.json")
firebase_admin.initialize_app(cred,{"databaseURL":"https://mailbox-83ab9.firebaseio.com/"})


motion_sensor = 37

GPIO.setmode(GPIO.BOARD)

GPIO.setup(motion_sensor,GPIO.IN, pull_up_down=GPIO.PUD_UP)
GPIO.setup(11,GPIO.OUT)
GPIO.output(11,GPIO.LOW)

def upload_images():
    ref = db.reference('/')
    x = strftime("%a, %d %b %Y %H:%M:%S", localtime())
    bucket = storage.bucket(name="mailbox-83ab9.appspot.com")
    i = 0
    while (i < 10):
        upload = bucket.blob("mail/{z}/{y}".format(z=x, y=i))
        upload.upload_from_filename(filename = "/home/pi/Documents/cse408/images/{z}.jpg".format(z=i))
        i += 1
    print('images have been uploaded')
    ref.child("paths").push(x)
def finger_search():
    found = False
    # Search for a finger
    # Tries to initialize the sensor
    try:
        f = PyFingerprint('/dev/ttyUSB0', 57600, 0xFFFFFFFF, 0x00000000)

        if ( f.verifyPassword() == False ):
            raise ValueError('The given fingerprint sensor password is wrong!')

    except Exception as e:
        print('The fingerprint sensor could not be initialized!')
        print('Exception message: ' + str(e))
        exit(1)
    # Gets some sensor information
    print('Currently used templates: ' + str(f.getTemplateCount()) +'/'+ str(f.getStorageCapacity()))

    # Tries to search the finger and calculate hash
    try:
        print('Waiting for finger...')
        timeout = time.time() + 9
    # Wait that finger is read
        while ( f.readImage() == False):
            #pass
            if time.time() > timeout:
                positionNumber = -1
                break
    # Converts read image to characteristics and stores it in charbuffer 1
        f.convertImage(0x01)

    # Searchs template
        result = f.searchTemplate()

        positionNumber = result[0]
        accuracyScore = result[1]

        if ( positionNumber == -1 ):
            print('No match found!')
            found = False
            return found
           # exit(0)
        else:
            print('Found template at position #' + str(positionNumber))
        print('The accuracy score is: ' + str(accuracyScore))

    # OPTIONAL stuff
    # Loads the found template to charbuffer 1
        f.loadTemplate(positionNumber, 0x01)

    # Downloads the characteristics of template loaded in charbuffer 1
        characterics = str(f.downloadCharacteristics(0x01)).encode('utf-8')

    # Hashes characteristics of template
        print('SHA-2 hash of template: ' + hashlib.sha256(characterics).hexdigest())
        found = True
        return found
    except Exception as e:
        print('Operation failed!')
        print('Exception message: ' + str(e))
        exit(1)
def finger_enroll():
    #  Enrolls new finger
    # Tries to initialize the sensor
    try:
        f = PyFingerprint('/dev/ttyUSB0', 57600, 0xFFFFFFFF, 0x00000000)

        if ( f.verifyPassword() == False ):
            raise ValueError('The given fingerprint sensor password is wrong!')

    except Exception as e:
        print('The fingerprint sensor could not be initialized!')
        print('Exception message: ' + str(e))
        exit(1)

    # Gets some sensor information
    print('Currently used templates: ' + str(f.getTemplateCount()) +'/'+ str(f.getStorageCapacity()))

    # Tries to enroll new finger
    try:
        print('Waiting for finger...')

        # Wait that finger is read
        while ( f.readImage() == False ):
            pass
        # Converts read image to characteristics and stores it in charbuffer 1
        f.convertImage(0x01)

        # Checks if finger is already enrolled
        result = f.searchTemplate()
        positionNumber = result[0]

        if ( positionNumber >= 0 ):
            print('Template already exists at position #' + str(positionNumber))
            # exit(0)

        print('Remove finger...')
        time.sleep(2)

        print('Waiting for same finger again...')

        # Wait that finger is read again
        while ( f.readImage() == False ):
            pass

        # Converts read image to characteristics and stores it in charbuffer 2
        f.convertImage(0x02)

        # Compares the charbuffers
        if ( f.compareCharacteristics() == 0 ):
       	    raise Exception('Fingers do not match')

    	# Creates a template
        f.createTemplate()

    	# Saves template at new position number
        positionNumber = f.storeTemplate()
        print('Finger enrolled successfully!')
        print('New template position #' + str(positionNumber))

    except Exception as e:
        print('Operation failed!')
        print('Exception message: ' + str(e))
        exit(1)
def finger_delete():
    # Deletes a finger from sensor
    # Tries to initialize the sensor
    try:
        f = PyFingerprint('/dev/ttyUSB0', 57600, 0xFFFFFFFF, 0x00000000)

        if ( f.verifyPassword() == False ):
            raise ValueError('The given fingerprint sensor password is wrong!')

    except Exception as e:
        print('The fingerprint sensor could not be initialized!')
        print('Exception message: ' + str(e))
        exit(1)

    # Gets some sensor information
    print('Currently used templates: ' + str(f.getTemplateCount()) +'/'+ str(f.getStorageCapacity()))

    # Tries to delete the template of the finger
    try:
        positionNumber = input('Please enter the template position you want to delete: ')
        positionNumber = int(positionNumber)

        if ( f.deleteTemplate(positionNumber) == True ):
            print('Template deleted!')

    except Exception as e:
        print('Operation failed!')
        print('Exception message: ' + str(e))
        exit(1)
def finger_image():
    # Reads image and download it
    # Tries to initialize the sensor
    try:
        f = PyFingerprint('/dev/ttyUSB0', 57600, 0xFFFFFFFF, 0x00000000)

        if ( f.verifyPassword() == False ):
            raise ValueError('The given fingerprint sensor password is wrong!')

    except Exception as e:
        print('The fingerprint sensor could not be initialized!')
        print('Exception message: ' + str(e))
        exit(1)

    # Gets some sensor information
    print('Currently used templates: ' + str(f.getTemplateCount()) +'/'+ str(f.getStorageCapacity()))

    # Tries to read image and download it
    try:
        print('Waiting for finger...')

        # Wait that finger is read
        while ( f.readImage() == False ):
            pass

        print('Downloading image (this take a while)...')

        imageDestination =  tempfile.gettempdir() + '/fingerprint.bmp'
        f.downloadImage(imageDestination)

        print('The image was saved to "' + imageDestination + '".')

    except Exception as e:
        print('Operation failed!')
        print('Exception message: ' + str(e))
        exit(1)
def finger_index():
    # Shows the template index table
    # Tries to initialize the sensor
    try:
        f = PyFingerprint('/dev/ttyUSB0', 57600, 0xFFFFFFFF, 0x00000000)

        if ( f.verifyPassword() == False ):
            raise ValueError('The given fingerprint sensor password is wrong!')

    except Exception as e:
        print('The fingerprint sensor could not be initialized!')
        print('Exception message: ' + str(e))
        exit(1)

    # Gets some sensor information
    print('Currently used templates: ' + str(f.getTemplateCount()) +'/'+ str(f.getStorageCapacity()))

    # Tries to show a template index table page
    try:
        page = input('Please enter the index page (0, 1, 2, 3) you want to see: ')
        page = int(page)

        tableIndex = f.getTemplateIndex(page)

        for i in range(0, len(tableIndex)):
            print('Template at position #' + str(i) + ' is used: ' + str(tableIndex[i]))

    except Exception as e:
        print('Operation failed!')
        print('Exception message: ' + str(e))
        exit(1)

def cleanupLights(signal, frame):
    GPIO.cleanup()
    sys.exit(0)

def main():
    """ choice = ''
    while True:
        choice = raw_input('Enter your choice!\n')
        if (choice  == 'search'):
            finger_search()
        elif (choice == 'enroll'):
	    finger_enroll()
        elif (choice == 'delete'):
	    finger_delete()
        elif (choice == 'index'):
	    finger_index()
        else:
	    break
    """

    signal.signal(signal.SIGINT, cleanupLights)
    isOpen = None
    oldIsOpen = None
    while True:
        oldIsOpen = isOpen
        isOpen = GPIO.input(motion_sensor)
        if (isOpen and (isOpen != oldIsOpen)):
            print("OPEN!")
            camera.take_pic()
            buzzer = finger_search()
            if buzzer == False:
                GPIO.output(11,GPIO.HIGH)
                time.sleep(3)
                GPIO.output(11,GPIO.LOW)
                upload_images()
        elif (isOpen != oldIsOpen):
            print("CLOSED!")

        time.sleep(.2)
main()
