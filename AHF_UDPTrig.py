#! /usr/bin/python
#-*-coding: utf-8 -*-

import RPi.GPIO as GPIO
import socket
from time import sleep
UDP_PORT = 5007	# special open port 
class AHF_UDPTrig:
    """
    Sends/receives UDP signals as to another pi to start/stop recording

    AHF_UDPTrig uses the socket module to do the UDP stuff, but it should be part of
    the default install
    """
    
    def __init__ (self, UDPlist_p, GPIOpin):
        """Makes a new AHF_UDPtrig object using passed in list of ip addresses.

        stores UDPlist in the new object
        sets hasUDP to false if object creation fails because of network error, else True
        """
        try: 
            self.UDPlist = UDPlist_p
            self.sock=socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            self.sock.bind (('', UDP_PORT))
            hasUDP= True
            if GPIOpin == 0:
                self.hasGPIO = False
            else:
                self.hasGPIO = True
                self.GPIOpin=GPIOpin
                GPIO.setmode (GPIO.BCM)
                GPIO.setwarnings (False)
                GPIO.setup (self.GPIOpin, GPIO.OUT)
        except socket.error:
            hasUDP = False
            print ('AHF_UDPTrig failed to create a socket.')


    def doTrigger (self, message):
        """
        Sends a UDP message to the stored list of  ip addresses
        """
        try:
            for address in self.UDPlist:
              self.sock.sendto (bytes (message, "utf-8"),(address, UDP_PORT))
        except socket.error as e:
            print ('AHF_UDPTrig failed to send a message: ' + str (e))

    def GPIOhighTrigger (self):
        if self.hasGPIO:
            GPIO.output (self.GPIOpin, GPIO.HIGH)

    def GPIOlowTrigger (self):
        if self.hasGPIO:
            GPIO.output (self.GPIOpin, GPIO.LOW)

    def getTrigger (self):
        """
        Waits for a UDP message and returns a string contaiing the message
        """
        data, addr=self.sock.recvfrom(1024)
        dataStr = data.decode("utf-8")
        return (addr[0], dataStr)
    
    
#for testing purposes
if __name__ == '__main__':
    hasUDP = True
    trigger = AHF_UDPTrig (('169.254.6.26',), 16)
    if hasUDP == True:
        message = 'hello_from_AHF_UDPTrig'
        trigger.doTrigger (message)
        sleep (1)
        trigger.GPIOhighTrigger ()
        sleep (5)
        trigger.GPIOlowTrigger ()
        trigger.doTrigger ('Stop')
