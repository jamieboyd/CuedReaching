#! /usr/bin/python
#-*-coding: utf-8 -*-

from time import time, sleep, localtime
from datetime import datetime
import RPi.GPIO as GPIO
from AHF_LickDetector import LickDetector, Simple_Logger
from AHF_UDPTrig import AHF_UDPTrig
from array import array
from PTSimpleGPIO import PTSimpleGPIO, Pulse, Train
import picamera
"""
Water valve,buzzer, touch sensor, suction valve
buzz the buzzer, put out a water drop
wait for touch sensor input with a timeout of 60 seconds
after a touch, wait 10 seconds, then do it again
record time of drops, time of touches

record video in circular buffer, save 10 seconds before touch,
20 seconds after a touch
"""

rewardPin = 17
suctionPin = 22
touchIRQ = 4
buzzerPin = 27
xcapPin = 12
UDPpin = 5
UDPreceivers = ('169.254.6.26',)
interTrialInterval = 6
lickTimeOut = 10
buzzFreq = 6000
buzzDuration = 0.1
rewardSize = 0.1
moviePreLickTime = 3
moviePostLickTime = 3
pathToData='/home/pi/Documents/' 

def main ():

    # get the mouse name from the user, used in making video names
    mouseName = input ('enter the name of the mouse:')
    # open a text file for writing trials, not that anything much happens that is not in the video
    today=localtime()
    textFP = open ('%s%s_%s_%s_%s.txt' % (pathToData, mouseName, today.tm_year, today.tm_mon, today.tm_mday), 'a')
    logger = Simple_Logger (textFP)
    # set up the hardware
    GPIO.setmode (GPIO.BCM)
    GPIO.setwarnings(False)
    GPIO.setup(xcapPin, GPIO.OUT)
    ld = LickDetector (touchIRQ, logger)
    buzzer = Train (PTSimpleGPIO.MODE_FREQ, buzzerPin, 0, buzzFreq, 0.5, buzzDuration, 1)
    buzzer.do_train()
    rewarder = Pulse (rewardPin, 0, 0.05, rewardSize, 1)
    rewarder.do_pulse()
    sleep (5)
    suction = Pulse (suctionPin, 0, 0.05, 0.5, 1)
    suction.do_pulse ()
    trigger = AHF_UDPTrig (UDPreceivers, UDPpin)
    camera = picamera.PiCamera(resolution = (320, 320), framerate = 60)
    #camera.contrast = 100
    camera.brightness = 35
    movieTime = moviePreLickTime + moviePostLickTime
    stream = picamera.PiCameraCircularIO (camera, seconds = movieTime)
    camera.start_preview(fullscreen = False, window = (0,0,320,320))
    # main loop for trials
    while (True):
        try:
            fileName = '{0:s}_{1:d}'.format(mouseName, round(time ()))
            trigger.doTrigger (fileName)
            sleep (1.0) # should be enough time for UDP message to be processed
            logger.writeToLogFile ('cameraStart')
            GPIO.output(xcapPin, GPIO.HIGH)
            camera.start_recording (stream, format = 'h264')
            trigger.GPIOhighTrigger()
            sleep (0.1)
            GPIO.output(xcapPin, GPIO.LOW)
            sleep (interTrialInterval)
            # buzz the buzzer and dispense a drop
            buzzer.do_train()
            rewarder.do_pulse()
            logger.writeToLogFile ('trialStart')
            # wait for a lick
            licks = ld.waitForLick (lickTimeOut, startFromZero = True)
            
            if licks > 0: # we had a lick, keep recording for a few more seconds,then write video to disk
                #GPIO.output(xcapPin, GPIO.HIGH);sleep (0.1);GPIO.output(xcapPin, GPIO.LOW)
                logger.writeToLogFile ('touchRecorded')
                lickTimeStr = str (round(time ()))
                sleep (moviePostLickTime)
            elif licks == -1:
                logger.writeToLogFile ('lickDetector reset')
                lickTimeStr = str (round(time ()))
                ld.resetDetector ()
            else:
                suction.do_pulse ()
                logger.writeToLogFile ('trialTimedOutWithNoLicks')
                lickTimeStr = str (round(time ()))

            trigger.GPIOlowTrigger()
            GPIO.output(xcapPin, GPIO.HIGH)
            camera.stop_recording()
            sleep (0.1);GPIO.output(xcapPin, GPIO.LOW)
            trigger.doTrigger ('Stop')
            movieName = '{0:s}{1:s}.h264'.format (pathToData, fileName)
            with open (movieName, 'wb') as fileOut:
                stream.copy_to (fileOut)
                stream.clear()
            logger.writeToLogFile ('movieFile:{0:s}'.format(movieName))
            sleep(2)

            
        except (KeyboardInterrupt) as e:
            print ('Exiting:', str (e))
            camera.stop_preview()
            camera.stop_recording ()
            textFP.close ()
            GPIO.cleanup()
            break
                
if __name__ == '__main__':
    main()
