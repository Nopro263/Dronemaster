# Dronemaster
a modern alternative to the Robomaster SDK for controlling DJI Tello EDU drones. \
This sdk is a result of my frustration with the official robomaster sdk and how other libraries handle specific things. \
It is based on the official [tello 3.0 protocol documentation](https://dl.djicdn.com/downloads/RoboMaster+TT/Tello_SDK_3.0_User_Guide_en.pdf), but is extended with undocumented features that were discovered by experiments. \
It harnesses the power of pythons async capabilities and also allows to control multiple drones at once.

## Basics
This section describes how the drone works, so you are able to efficiently work with this sdk and avoid common pitfalls. \
Firstly the drone can operate in two basic modes which can be selected with the slider on the side of the extension module: 
- `ap-mode`: the drone connects to a preexisting wifi
- `sta-mode`: the drone creates its own wifi

**When operating in `ap-mode` and using static dhcp entries, the drone sometimes receives a wrong ip**

The protocol is based on udp, so packet-loss due to an unstable connection might lead to timeouts (this sdk tries its best to mitigate this, but it is not always successful). \
Sometimes the error is not due to the programmer or the sdk, but simply due to the drone itself. \
The drone has been observed as reporting ok to a takeoff-request but then staying firmly on the ground even with enough charge, so also account for such failures.

## Specs
The drone is equipped with some sensors that might be interesting.
- gyro: to measure *roll*, *pitch* and *yaw* in degrees
- accelerometer: to measure the acceleration in *x*, *y* and *z* direction relative to the current orientation. Note that you should remove gravity from these by using the current orientation.
- barometer: to estimate the *elevation* of the drone in meters
- downwards time-of-flight sensor: to accurately measure the *height above ground*
- forwards time-of-flight sensor: to measure the *distance to an object* (located on the extension module)
- internal temperature: measures the *internal temperature* (above ~100°C it no longer takes off and above ~105°C it shuts down)
- front camera: positioned at an angle of ~13° downwards that records 720P or 480P in H264
- downwards camera: black and white camera without an IR-filter
- velocity calculation: the internal chip calculates the velocity in *x*, *y* and *z* direction in global space. It uses the downwards camera, so if there is not enough detail in its picture these speeds are 0
- mission-pad detection: this is currently not usable with this sdk

## Installing
To install this sdk, simply use pip \
`pip install dronemaster` \
or when using the simulator \
`pip install dronemaster[simulator]`

## Simulator
This sdk provides a crude simulator so anybody without a drone is able to test parts of their program. \
First run `pip install dronemaster[simulator]` to install the required dependencies. \
Then start the simulator with `python3 -m dronemaster [IP]` where `[IP]` is the ip-address to listen on. \
You can now connect to your own ip as if it would be a drone.

## Api overview
The exact behavior of each function is documented in docstrings. This section should only give a very basic overview.

### Logging
The sdk uses the python logging module, so you are able to configure it to your liking.
- DEBUG logs exactly what raw packets are sent and received (even repeated ones)
- INFO only logs successful commands and their response
- WARN logs unexpected data
- ERROR logs invalid answers to commands and timeouts

To access the logger, use `dronemaster.command_logger`

### Connecting
First, create the `dronemaster.Drone` object with the target-ip. \
Then call the `drone.initialize()` function to connect with it. \
You should periodically call the `drone.keepalive()` function to stop the drone from automatically landing.

### Flying
To control the flight, use the flight object received by `drone.flight`. \
To learn more, visit the examples or inspect it in your IDE

### Extension module
Access the top-rgb-led via `drone.rgb` and the matrix via `drone.matrix`

### Configuring the video
To configure the video (like resolution, fps, bitrate and selected camera) use `drone.video`

### Configuring the drone
You can configure the drone by using functions like `drone.set_own_wifi(ssid, passwd)` or `drone.set_connecting_wifi(ssid, passwd)`

### Receiving state information
The last state object is always available at `drone.last_state` \
Register a callback to be called on a new packet with `drone.state_subscribe(async_callback)` where async_callback is an async function which receives one parameter with type `dronemaster.DroneState`

### Some useful commands
After establishing the connection, you can use many features like:
- `drone.state_subscribe(...)` to subscribe to the drones state (see `dronemaster.DroneState`)
- `drone.serial_number()` to get the serial number
- `drone.battery()` to get the current battery charge
- `drone.tof()` to read the current height
- `drone.ext_tof()` to read the distance forwards
- `drone.keepalive()` call this to keep the drone in the air without sending other commands
- `drone.reboot()` reboot the drone and disconnect it
- `drone.matrix.set_brightness(...)` set the brightness of the led matrix
- `drone.matrix.set_pattern(...)` to set the pattern of the led matrix
- `drone.rgb.set(...)` sets the color of the top led
- `drone.rgb.pulse(..., ...)` pulses the top led in the specific color
- `drone.rgb.flash(..., ..., ...)` flashed the top led between the two colors
- `drone.video.streamon()` to enable the video stream
- `drone.video.streamoff()` to stop the video stream
- `drone.video.downvision(...)` to switch the used camera
- `drone.video.setfps(...)` to set the cameras fps
- `drone.video.setbitrate(...)` to set the cameras bitrate in Mbps
- `drone.video.setresolution(...)` to set the front-facing cameras resolution
- `drone.flight.takeoff()` to takeoff
- `drone.flight.land()` to land
- `drone.flight.rc(..., ..., ..., ...)` to set roll, pitch, yaw and throttle
- `drone.flight.stop()` to stop moving and start hovering
- `drone.flight.emergency()` to stop all motors \
and many more...

## Examples
These are the two most important ones. See more [here](https://github.com/Nopro263/Dronemaster/tree/main/examples)

### Simple flight
```python
import asyncio
import dronemaster

import logging
logging.basicConfig(format="%(asctime)s [%(name)s] [%(levelname)s] %(message)s") # dronemaster uses the logging module internally
dronemaster.command_logger.setLevel(logging.WARNING) # do not log raw commands
# DEBUG logs exactly what commands are sent and received (even repeated ones)
# INFO only logs successful commands and their response
# WARN logs unexpected data
# ERROR logs invalid answers to commands and timeouts

async def main():
    # create the drone, but don't connect
    ep_drone = dronemaster.Drone("127.0.0.1")

    # mark the drone as active and connect to it
    await ep_drone.initialize()

    serial = await ep_drone.serial_number()
    battery = await ep_drone.battery()
    print(f"Connected with drone '{serial}' with {battery}%")

    ep_flight = ep_drone.flight

    # takeoff and wait for completion (up to 20s)
    await ep_flight.takeoff()

    # fly forwards 20cm
    await ep_flight.forward(20, timeout=7)

    # land again
    await ep_flight.land()

if __name__ == '__main__':
    asyncio.run(main())
```

### Video receiving
```python
import asyncio
import dronemaster
import cv2

import logging
logging.basicConfig(format="%(asctime)s [%(name)s] [%(levelname)s] %(message)s") # dronemaster uses the logging module internally
dronemaster.command_logger.setLevel(logging.WARNING) # do not log raw commands

async def main():
    # create the drone, but don't connect
    ep_drone = dronemaster.Drone("127.0.0.1")

    # mark the drone as active and connect to it
    await ep_drone.initialize()

    serial = await ep_drone.serial_number()
    battery = await ep_drone.battery()
    print(f"Connected with drone '{serial}' with {battery}%")

    await ep_drone.video.set_video_port(11112) # per default, port 11111 is used

    await ep_drone.video.streamon()

    # uncomment to use the downwards black and white camera
    #await ep_drone.video.downvision(True)

    # listen on all ips on port 11112
    # the drone sends the video in H264 format with an I-Frame every few seconds
    cap = cv2.VideoCapture("udp://0.0.0.0:11112")

    while True:
        if cap.isOpened():
            ret, frame = cap.read()
            cv2.imshow('live stream', frame)
            await asyncio.sleep(1/60) # important to allow the sdk to read new commands
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break
    
    cap.release()
    cv2.destroyAllWindows()

    await ep_drone.video.streamoff()
    

if __name__ == '__main__':
    asyncio.run(main())
```