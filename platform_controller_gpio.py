from __future__ import print_function
import RPi.GPIO as GPIO
import time
import threading
import websockets
import asyncio
from circuits import Debugger, handler
from circuits.net.sockets import TCPServer
from picamera.array import PiRGBArray
from picamera import PiCamera
from collections import deque
import numpy as np
import datetime
import imutils
import time
import pigpio
import cv2

# motor
stopFlag = False
pinOne = 17 
pinTwo = 27
pinThree = 23
pinFour = 24

#cam
pinFive = 18
pi = pigpio.pi()

#dma pis
dmaPiOne = pigpio.pi()
dmaPiTwo = pigpio.pi()
dmaPiThree = pigpio.pi()
dmaPiFour = pigpio.pi()

time.sleep(1)
      
class MSGWorker (threading.Thread):
  def __init__(self):
    threading.Thread.__init__(self)
    self.connected = set()

  def run(self):
    self.m1 = GPIO.LOW
    self.m2 = GPIO.LOW
    self.m3 = GPIO.LOW
    self.m4 = GPIO.LOW

    self.status = "stopped"
    self.speed = 1.0
    self.cycle = 2200
    self.addCycle = 0
    pi.set_servo_pulsewidth(18,self.cycle)
    time.sleep(1)
    pi.set_servo_pulsewidth(18,0)
 
    while True: 
      if self.status == "running":

        if self.cycle < 600:
           self.cycle = 600

        if self.cycle > 2400:
           self.cycle = 2400


        if self.cycle >= 600 and self.cycle <= 2400:
          pi.set_servo_pulsewidth(18,self.cycle)
          self.cycle = self.cycle + self.addCycle

      time.sleep(0.001)
           
  def picture(self):
      camera.capture('/home/pi/Desktop/image.jpg')

  def forward(self):
      dmaPiOne.set_PWM_dutycycle(17,int(100 * float(self.speed)))
      dmaPiTwo.set_PWM_dutycycle(23,int(100 * float(self.speed)))

  def left(self):
      print("left")
      dmaPiOne.set_PWM_dutycycle(23,int(100 * float(self.speed)))
      dmaPiTwo.set_PWM_dutycycle(27,int(100 * float(self.speed)))

  def right(self):
      print("right")
      dmaPiOne.set_PWM_dutycycle(17,int(100 * float(self.speed)))
      dmaPiTwo.set_PWM_dutycycle(24,int(100 * float(self.speed)))

  def camUp(self):
      print(self.cycle)
      self.status = "running"
      self.addCycle = - 4.8

  def camDown(self):
      print(self.cycle)
      self.status = "running"
      self.addCycle = + 4.8

  def camStop(self):
      print(self.cycle)
      self.status = "stopped"
      pi.set_servo_pulsewidth(18,0)
      self.addCycle = 0
      
  def backward(self):
      print("backward")
      dmaPiThree.set_PWM_dutycycle(27,int(100 * float(self.speed)))
      dmaPiFour.set_PWM_dutycycle(24,int(100 * float(self.speed)))

  def stop(self):
      print("stop")
      dmaPiOne.set_servo_pulsewidth(17,0)
      dmaPiTwo.set_servo_pulsewidth(23,0)
      dmaPiThree.set_servo_pulsewidth(27,0)
      dmaPiFour.set_servo_pulsewidth(24,0)
      
      
  @asyncio.coroutine
  def handler(self, websocket, path):
    self.connected.add(websocket)
    try:   
      name = yield from websocket.recv()
      commaindex = name.find(",")
      commandlength = len(name)
      direction = name[0:commaindex]
      self.speed = name[commaindex+1:commandlength]
    
      print(direction+':'+self.speed)
      
      if(direction == "right"):
          self.right()
          
      if(direction == "left"):
          self.left()

      if(direction == "forward"):
          self.forward()

      if(direction == "backward"):
          self.backward()

      if(direction == "stop"):
          self.stop()

      if(name == "picture"):
          self.picture()

      if(name == "camstop"):
          self.camStop()

      if(name == "camup"):
          self.camUp()

      if(name == "camdown"):
          self.camDown()
          
    except websockets.exceptions.ConnectionClosed:
      pass
    

  def sendData(self, data):
    for websocket in self.connected.copy():
      print("Sending data: %s" % data)
      coro =yield from websocket.send(data)
      future = asyncio.run_coroutine_threadsafe(coro, loop)

if __name__ == "__main__":
  print('robot Server')
  global motorOne
  global motorTwo
  motorOne = 0
  motorTwo = 0
  msgWorker = MSGWorker()
  
  try:
    msgWorker.start()
    ws_server = websockets.serve(msgWorker.handler, '192.168.178.61', 8080)
    loop = asyncio.get_event_loop()
    loop.run_until_complete(ws_server)
    loop.run_forever()
  except KeyboardInterrupt:
    stopFlag = True
    print("Exiting program...")
  
