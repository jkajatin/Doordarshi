import RPi.GPIO as GPIO
import requests
import time
import subprocess
import os
import cv2
import pytesseract
from datetime import datetime
from threading import Timer

# GPIO Setup
BUTTON_PIN = 17
GPIO.setmode(GPIO.BCM)
GPIO.setup(BUTTON_PIN, GPIO.IN, pull_up_down=GPIO.PUD_UP)

# Constants
SERVER_URL = "http://192.168.218.209:5000/upload"  # ? Replace with actual IP
DOUBLE_CLICK_TIME = 0.4  # seconds
LONG_PRESS_TIME = 1.5    # seconds

# Globals
last_description = "No previous description available."
click_count = 0
timer = None
press_start = 0


def perform_ocr(image_path):
    print("Performing OCR...")
    image = cv2.imread(image_path)
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    text = pytesseract.image_to_string(gray)
    print("OCR Result:", text.strip())
    return text.strip() if text.strip() else "No readable text found."


def describe_image():
    global last_description
    print("Capturing image for description...")
    os.system(f'espeak -s 170 -a 200 "Capturing image for description."')
    filename = f"/home/shubh/Desktop/MDServer_Images/image_{datetime.now().strftime('%Y%m%d_%H%M%S')}.jpg"
    subprocess.run(["libcamera-jpeg", "-o", filename])

    try:
        files = {'image': open(filename, 'rb')}
        print("Sending image to server...")
        response = requests.post(SERVER_URL, files=files, timeout=60)
        last_description = response.text
        print("Description:", last_description)
    except Exception as e:
        last_description = "Error contacting."
        print(last_description, str(e))

    os.system(f'espeak -s 170 -a 200 "{last_description}"')


def repeat_last():
    print("Repeating last description.")
    os.system(f'espeak -s 170 -a 200 "Long press detected: repeating last description."')
    os.system(f'espeak -s 170 -a 200 "{last_description}"')


def run_ocr():
    print("Capturing image for OCR...")
    os.system(f'espeak -s 170 -a 200 "Capturing image for OCR."')
    filename = f"/home/shubh/Desktop/MDServer_Images/ocr_{datetime.now().strftime('%Y%m%d_%H%M%S')}.jpg"
    subprocess.run(["libcamera-jpeg", "-o", filename])
    text = perform_ocr(filename)
    os.system(f'espeak -s 170 -a 200 "{text}"')


def single_click_action():
    global click_count
    if click_count == 1:
        describe_image()
    elif click_count == 2:
        run_ocr()
    click_count = 0


def button_callback(channel):
    global click_count, timer, press_start

    if GPIO.input(BUTTON_PIN) == GPIO.LOW:
        press_start = time.time()
    else:
        press_duration = time.time() - press_start

        if press_duration >= LONG_PRESS_TIME:
            if timer:
                timer.cancel()
            click_count = 0
            repeat_last()
        else:
            click_count += 1
            if timer:
                timer.cancel()
            timer = Timer(DOUBLE_CLICK_TIME, single_click_action)
            timer.start()


# Attach interrupt to button
GPIO.add_event_detect(BUTTON_PIN, GPIO.BOTH, callback=button_callback, bouncetime=50)

print("Ready. Short = describe | Long = repeat | Double = OCR")
os.system(f'espeak -s 170 -a 200 "Ready to capture image."')
os.system(f'espeak -s 150 -a 200 "Press button: Short = new image, Long = repeat, Double = OCR."')

try:
    while True:
        time.sleep(0.1)

except KeyboardInterrupt:
    GPIO.cleanup()

