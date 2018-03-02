# robot_platform
The platform consists of modules you can start seperately in order to enable features you actually need.
The intercommuniaction of the processes are done via websockets if needed. Communication via websockets sure has its
downsides speaking of latency, network and wifi stability and so on but its great if you have more then one client for
controlling, like an app or several webclients for control or monitoring tasks.

## Getting Started

For now just start the files ! You may need to start other modules first in order
to run your module properly 

Startig is easy 
  - "platform_controller_gpio" once started you can send commands to the controller via a generic client
  - "platform_vision_opencv" does some computervision and tracks a green colorblob sends coords to controller

### Prerequisites

Raspberry Pi 3
Raspberry Pi Camera Module

### Installing

A number of libs have to be installed.

In order to run opencv on your pi just follow the instructions of Adrian Rosebrock. Great guy btw ! :)

https://www.pyimagesearch.com/2015/02/23/install-opencv-and-python-on-your-raspberry-pi-2-and-b/
 

- websockets
- numpy
- picamera
 
Depending on your system i would recommend to do it with npm.


## Acknowledgments

I want to use that platform over an extended period of time i want to see whats possible on the pi when 
so many processes are executed at once. Just testing the limits !
