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

# Api documentation

* [dronemaster.Drone](#dronemaster.Drone)
  * [DroneState](#dronemaster.Drone.DroneState)
    * [pitch](#dronemaster.Drone.DroneState.pitch)
    * [roll](#dronemaster.Drone.DroneState.roll)
    * [yaw](#dronemaster.Drone.DroneState.yaw)
    * [vgx](#dronemaster.Drone.DroneState.vgx)
    * [vgy](#dronemaster.Drone.DroneState.vgy)
    * [vgz](#dronemaster.Drone.DroneState.vgz)
    * [bat](#dronemaster.Drone.DroneState.bat)
    * [templ](#dronemaster.Drone.DroneState.templ)
    * [temph](#dronemaster.Drone.DroneState.temph)
    * [tof](#dronemaster.Drone.DroneState.tof)
    * [h](#dronemaster.Drone.DroneState.h)
    * [time](#dronemaster.Drone.DroneState.time)
    * [agx](#dronemaster.Drone.DroneState.agx)
    * [agy](#dronemaster.Drone.DroneState.agy)
    * [agz](#dronemaster.Drone.DroneState.agz)
    * [baro](#dronemaster.Drone.DroneState.baro)
    * [last\_update](#dronemaster.Drone.DroneState.last_update)
    * [delta](#dronemaster.Drone.DroneState.delta)
  * [Drone](#dronemaster.Drone.Drone)
    * [state\_subscribe](#dronemaster.Drone.Drone.state_subscribe)
    * [initialize](#dronemaster.Drone.Drone.initialize)
    * [serial\_number](#dronemaster.Drone.Drone.serial_number)
    * [battery](#dronemaster.Drone.Drone.battery)
    * [flight\_time](#dronemaster.Drone.Drone.flight_time)
    * [sdk\_version](#dronemaster.Drone.Drone.sdk_version)
    * [get\_hardware](#dronemaster.Drone.Drone.get_hardware)
    * [wifi\_serial](#dronemaster.Drone.Drone.wifi_serial)
    * [wifi\_version](#dronemaster.Drone.Drone.wifi_version)
    * [ext\_tof](#dronemaster.Drone.Drone.ext_tof)
    * [tof](#dronemaster.Drone.Drone.tof)
    * [keepalive](#dronemaster.Drone.Drone.keepalive)
    * [set\_own\_wifi](#dronemaster.Drone.Drone.set_own_wifi)
    * [set\_connecting\_wifi](#dronemaster.Drone.Drone.set_connecting_wifi)
    * [send\_raw\_command](#dronemaster.Drone.Drone.send_raw_command)
    * [reboot](#dronemaster.Drone.Drone.reboot)
    * [disconnect](#dronemaster.Drone.Drone.disconnect)
  * [Video](#dronemaster.Drone.Video)
    * [streamon](#dronemaster.Drone.Video.streamon)
    * [streamoff](#dronemaster.Drone.Video.streamoff)
    * [downvision](#dronemaster.Drone.Video.downvision)
    * [setfps](#dronemaster.Drone.Video.setfps)
    * [setbitrate](#dronemaster.Drone.Video.setbitrate)
    * [setresolution](#dronemaster.Drone.Video.setresolution)
    * [set\_video\_port](#dronemaster.Drone.Video.set_video_port)
  * [Flight](#dronemaster.Drone.Flight)
    * [takeoff](#dronemaster.Drone.Flight.takeoff)
    * [forward](#dronemaster.Drone.Flight.forward)
    * [back](#dronemaster.Drone.Flight.back)
    * [up](#dronemaster.Drone.Flight.up)
    * [down](#dronemaster.Drone.Flight.down)
    * [left](#dronemaster.Drone.Flight.left)
    * [right](#dronemaster.Drone.Flight.right)
    * [clockwise](#dronemaster.Drone.Flight.clockwise)
    * [counterclockwise](#dronemaster.Drone.Flight.counterclockwise)
    * [land](#dronemaster.Drone.Flight.land)
    * [stop](#dronemaster.Drone.Flight.stop)
    * [emergency](#dronemaster.Drone.Flight.emergency)
    * [motoron](#dronemaster.Drone.Flight.motoron)
    * [motoroff](#dronemaster.Drone.Flight.motoroff)
    * [flip](#dronemaster.Drone.Flight.flip)
    * [throwfly](#dronemaster.Drone.Flight.throwfly)
    * [speed](#dronemaster.Drone.Flight.speed)
    * [rc](#dronemaster.Drone.Flight.rc)
  * [RGBLed](#dronemaster.Drone.RGBLed)
    * [set](#dronemaster.Drone.RGBLed.set)
    * [pulse](#dronemaster.Drone.RGBLed.pulse)
    * [flash](#dronemaster.Drone.RGBLed.flash)
  * [Matrix](#dronemaster.Drone.Matrix)
    * [set\_brightness](#dronemaster.Drone.Matrix.set_brightness)
    * [set\_pattern](#dronemaster.Drone.Matrix.set_pattern)

<a id="dronemaster.Drone"></a>

# dronemaster.Drone

<a id="dronemaster.Drone.DroneState"></a>

## DroneState Objects

```python
class DroneState(TypedDict)
```

The current state of the drone, reported ~10x per second.

**Notes**:

  - the velocities are calculated by using the downwards camera, so when flying low or above featureless ground, it may be wrongly reported as 0

<a id="dronemaster.Drone.DroneState.pitch"></a>

## pitch

pitch in degrees

<a id="dronemaster.Drone.DroneState.roll"></a>

## roll

roll in degrees

<a id="dronemaster.Drone.DroneState.yaw"></a>

## yaw

yaw in degrees

<a id="dronemaster.Drone.DroneState.vgx"></a>

## vgx

velocity in x-direction (forwards/backwards) in dm/s

<a id="dronemaster.Drone.DroneState.vgy"></a>

## vgy

velocity in y-direction (left/right) in dm/s

<a id="dronemaster.Drone.DroneState.vgz"></a>

## vgz

velocity in z-direction (up/down) in dm/s

<a id="dronemaster.Drone.DroneState.bat"></a>

## bat

battery percentage

<a id="dronemaster.Drone.DroneState.templ"></a>

## templ

the lower range of the internal temperature sensor in °C

<a id="dronemaster.Drone.DroneState.temph"></a>

## temph

the upper range of the internal temperature sensor in °C

<a id="dronemaster.Drone.DroneState.tof"></a>

## tof

the vertical distance to ground in cm. reported as 10 if out of range

<a id="dronemaster.Drone.DroneState.h"></a>

## h

the calculated height, note that this only works in flight

<a id="dronemaster.Drone.DroneState.time"></a>

## time

number of seconds the drone has been flying

<a id="dronemaster.Drone.DroneState.agx"></a>

## agx

acceleration in x-direction in cm/s²

<a id="dronemaster.Drone.DroneState.agy"></a>

## agy

acceleration in y-direction in cm/s²

<a id="dronemaster.Drone.DroneState.agz"></a>

## agz

acceleration in z-direction in cm/s²

<a id="dronemaster.Drone.DroneState.baro"></a>

## baro

Height above sea level as reported by the barometer in m

<a id="dronemaster.Drone.DroneState.last_update"></a>

## last\_update

unix timestamp of the last update

<a id="dronemaster.Drone.DroneState.delta"></a>

## delta

time in seconds between the last two state packets

<a id="dronemaster.Drone.Drone"></a>

## Drone Objects

```python
class Drone()
```

The main class to control the drone.

**Example**:

```python

drone = Drone(DRONE_IP)
await drone.initialize()

# calls my_callback_function ~10x per second
drone.state_subscribe(my_callback_function)

# you should call this every few seconds to know if the drone has disconnected
await drone.keepalive()

# everything flight-related
flight = drone.flight

# control the rgb-led on top of the extension-module
rgb = drone.rgb

# control the extension-modules led-matrix
matrix = drone.matrix

# everything video-related
video = drone.video
```

<a id="dronemaster.Drone.Drone.state_subscribe"></a>

## state\_subscribe

```python
def state_subscribe(callable: Callable[[DroneState], Coroutine[Any, Any,
                                                               None]])
```

Adds the callable to the list of functions to be called when a new state is available

**Arguments**:

- `callable`: The async function to be called when a new state-packet is received

<a id="dronemaster.Drone.Drone.initialize"></a>

## initialize

```python
async def initialize() -> None
```

Initializes the drone connection and optionally starts the communication channel.

This function must be called before any other

**Raises**:

- `ProtocolError`: raised when not receiving `ok`
- `TimeoutError`: raised when not answering after 2.5s

<a id="dronemaster.Drone.Drone.serial_number"></a>

## serial\_number

```python
async def serial_number() -> str
```

Queries the drone for its serial number in the format `[A-Z0-9]{14}`

**Raises**:

- `ProtocolError`: raised when not receiving the correct format
- `TimeoutError`: raised when not answering after 5s

**Returns**:

the serial number in the format `[A-Z0-9]{14}`

<a id="dronemaster.Drone.Drone.battery"></a>

## battery

```python
async def battery() -> int
```

Queries the drone for its current battery charce percentage from 0-100

**Raises**:

- `ProtocolError`: raised when not receiving the battery percentage
- `TimeoutError`: raised when not answering after 5s

**Returns**:

the battery percentage

<a id="dronemaster.Drone.Drone.flight_time"></a>

## flight\_time

```python
async def flight_time() -> int
```

Gets the time the motors have been running

**Raises**:

- `ProtocolError`: raised when not receiving the battery percentage
- `TimeoutError`: raised when not answering after 5s

**Returns**:

the motor-time in seconds

<a id="dronemaster.Drone.Drone.sdk_version"></a>

## sdk\_version

```python
async def sdk_version() -> int
```

Gets current sdk version (sometimes reported as 20 or 30)

**Raises**:

- `ProtocolError`: raised when not receiving the battery percentage
- `TimeoutError`: raised when not answering after 5s

**Returns**:

the sdk version

<a id="dronemaster.Drone.Drone.get_hardware"></a>

## get\_hardware

```python
async def get_hardware() -> Literal["TELLO", "RMTT"]
```

Checks if the drone is connected to the extension module

**Raises**:

- `ProtocolError`: raised when not receiving the battery percentage
- `TimeoutError`: raised when not answering after 5s

**Returns**:

`RMTT` if connected to the extension module, else `TELLO`

<a id="dronemaster.Drone.Drone.wifi_serial"></a>

## wifi\_serial

```python
async def wifi_serial() -> str
```

Gets the wifi serial number

**Raises**:

- `ProtocolError`: raised when not receiving the battery percentage
- `TimeoutError`: raised when not answering after 5s

**Returns**:

the wifi serial number

<a id="dronemaster.Drone.Drone.wifi_version"></a>

## wifi\_version

```python
async def wifi_version() -> str
```

Gets the wifi version

**Raises**:

- `ProtocolError`: raised when not receiving the battery percentage
- `TimeoutError`: raised when not answering after 5s

**Returns**:

the wifi version in the format `wifivx.x.x.x`

<a id="dronemaster.Drone.Drone.ext_tof"></a>

## ext\_tof

```python
async def ext_tof()
```

Reads the horizontal distance of the drone to the front.

**Raises**:

- `ProtocolError`: raised when not receiving data in the correct format
- `TimeoutError`: raised when not answering after 2.5s

**Returns**:

the horizontal distance to the front in mm or `None` if out of range

<a id="dronemaster.Drone.Drone.tof"></a>

## tof

```python
async def tof() -> Optional[int]
```

Reads the vertical distance of the drone to ground.

**Raises**:

- `ProtocolError`: raised when not receiving data in the correct format
- `TimeoutError`: raised when not answering after 2.5s

**Returns**:

the vertical distance to ground in mm or `None` if out of range

<a id="dronemaster.Drone.Drone.keepalive"></a>

## keepalive

```python
async def keepalive() -> bool
```

Sends a "ping" packet to the drone to stop it from landing automatically, but only if there is no currently waiting command

**Raises**:

- `ProtocolError`: raised when not receiving `ok`
- `TimeoutError`: raised when not answering after 2.5s

**Returns**:

True when the ping was successful, False when it was skipped

<a id="dronemaster.Drone.Drone.set_own_wifi"></a>

## set\_own\_wifi

```python
async def set_own_wifi(ssid: str, pwd: str) -> None
```

Sets the ssid/password to use when the drone creates its own wifi.

Note that the drone adds a `RMTT-` or `TELLO-` prefix to the ssid.
The drone reboots after 3s, so you have to manually reconnect

**Arguments**:

- `ssid`: the drone-wifis ssid
- `pwd`: the password

**Raises**:

- `ProtocolError`: raised when not receiving `ok`
- `TimeoutError`: raised when not answering after 5s

<a id="dronemaster.Drone.Drone.set_connecting_wifi"></a>

## set\_connecting\_wifi

```python
async def set_connecting_wifi(ssid: str, pwd: str) -> None
```

Sets the ssid/password of an existing wifi to connect to.

Note that the drone sometimes receives other/incorrect ip-adresses.
The drone reboots after 3s, so you have to manually reconnect

**Arguments**:

- `ssid`: the wifis ssid
- `pwd`: the password

**Raises**:

- `ProtocolError`: raised when not receiving `ok`
- `TimeoutError`: raised when not answering after 5s

<a id="dronemaster.Drone.Drone.send_raw_command"></a>

## send\_raw\_command

```python
async def send_raw_command(command,
                           wait_for_answer: bool = True,
                           timeout: float = 1) -> Optional[str]
```

Sends a raw command to the drone. Intended for debugging/manual mode

**Arguments**:

- `wait_for_answer`: if the code expects an answer
- `timeout`: when expecting an answer, how long to wait

**Raises**:

- `ProtocolError`: should never happen
- `TimeoutError`: raised when not answering after 5 * timeout

**Returns**:

the answer or `None` if no answer is expected

<a id="dronemaster.Drone.Drone.reboot"></a>

## reboot

```python
def reboot() -> None
```

Reboots the drone and closes the connection, so you have to manually reconnect with it

<a id="dronemaster.Drone.Drone.disconnect"></a>

## disconnect

```python
def disconnect() -> None
```

disconnect from the drone

<a id="dronemaster.Drone.Video"></a>

## Video Objects

```python
class Video(Module)
```

<a id="dronemaster.Drone.Video.streamon"></a>

## streamon

```python
async def streamon() -> None
```

Starts the stream so the drone sends the H264 stream to port 11111

**Raises**:

- `ProtocolError`: raised when not receiving `ok`
- `TimeoutError`: raised when not answering after 5s

<a id="dronemaster.Drone.Video.streamoff"></a>

## streamoff

```python
async def streamoff() -> None
```

Stops the video stream

**Raises**:

- `ProtocolError`: raised when not receiving `ok`
- `TimeoutError`: raised when not answering after 5s

<a id="dronemaster.Drone.Video.downvision"></a>

## downvision

```python
async def downvision(on: bool) -> None
```

Switches the used camera.

**Arguments**:

- `on`: if the downwards camera should be used

**Raises**:

- `ProtocolError`: raised when not receiving `ok`
- `TimeoutError`: raised when not answering after 5s

<a id="dronemaster.Drone.Video.setfps"></a>

## setfps

```python
async def setfps(fps: Literal["high", "middle", "low"]) -> None
```

Sets the streams fps to

- `high` -> 30fps
- `middle` -> 15fps
- `low` -> 5fps

**Arguments**:

- `fps`: the requested fps

**Raises**:

- `ProtocolError`: raised when not receiving `ok`
- `TimeoutError`: raised when not answering after 5s

<a id="dronemaster.Drone.Video.setbitrate"></a>

## setbitrate

```python
async def setbitrate(bitrate: Literal["auto", 1, 2, 3, 4, 5]) -> None
```

Sets the streams maximum bitrate to auto or the requested Mbps

**Arguments**:

- `bitrate`: the bitrate in Mbps or `auto`

**Raises**:

- `ProtocolError`: raised when not receiving `ok`
- `TimeoutError`: raised when not answering after 5s

<a id="dronemaster.Drone.Video.setresolution"></a>

## setresolution

```python
async def setresolution(resolution: Literal["high", "low"]) -> None
```

Sets the video streams resolution

- `high` -> 720P
- `low` -> 480P

**Arguments**:

- `resolution`: the requested resolution

**Raises**:

- `ProtocolError`: raised when not receiving `ok`
- `TimeoutError`: raised when not answering after 5s

<a id="dronemaster.Drone.Video.set_video_port"></a>

## set\_video\_port

```python
async def set_video_port(port: int) -> None
```

Sets the port the drone should send the video stream

**Arguments**:

- `port`: the port to send the stream to [1024,65535]

**Raises**:

- `ProtocolError`: raised when not receiving `ok`
- `TimeoutError`: raised when not answering after 5s

<a id="dronemaster.Drone.Flight"></a>

## Flight Objects

```python
class Flight(Module)
```

<a id="dronemaster.Drone.Flight.takeoff"></a>

## takeoff

```python
async def takeoff() -> None
```

Tries to takeoff

**Raises**:

- `ProtocolError`: raised when not receiving `ok`
- `TimeoutError`: raised when not answering after 20s

<a id="dronemaster.Drone.Flight.forward"></a>

## forward

```python
async def forward(dist: int, timeout: float = 5) -> None
```

The drone flies `dist` cm forwards.

**Arguments**:

- `dist`: distance in cm in the range [20, 500]
- `timeout`: the timeout in seconds

**Raises**:

- `ProtocolError`: raised when not receiving `ok`
- `TimeoutError`: raised when not answering after `timeout`

<a id="dronemaster.Drone.Flight.back"></a>

## back

```python
async def back(dist: int, timeout: float = 5) -> None
```

The drone flies `dist` cm backwards.

**Arguments**:

- `dist`: distance in cm in the range [20, 500]
- `timeout`: the timeout in seconds

**Raises**:

- `ProtocolError`: raised when not receiving `ok`
- `TimeoutError`: raised when not answering after `timeout`

<a id="dronemaster.Drone.Flight.up"></a>

## up

```python
async def up(dist: int, timeout: float = 5) -> None
```

The drone flies `dist` cm upwards.

**Arguments**:

- `dist`: distance in cm in the range [20, 500]
- `timeout`: the timeout in seconds

**Raises**:

- `ProtocolError`: raised when not receiving `ok`
- `TimeoutError`: raised when not answering after `timeout`

<a id="dronemaster.Drone.Flight.down"></a>

## down

```python
async def down(dist: int, timeout: float = 5) -> None
```

The drone flies `dist` cm downwards.

**Arguments**:

- `dist`: distance in cm in the range [20, 500]
- `timeout`: the timeout in seconds

**Raises**:

- `ProtocolError`: raised when not receiving `ok`
- `TimeoutError`: raised when not answering after `timeout`

<a id="dronemaster.Drone.Flight.left"></a>

## left

```python
async def left(dist: int, timeout: float = 5) -> None
```

The drone flies `dist` cm to the left.

**Arguments**:

- `dist`: distance in cm in the range [20, 500]
- `timeout`: the timeout in seconds

**Raises**:

- `ProtocolError`: raised when not receiving `ok`
- `TimeoutError`: raised when not answering after `timeout`

<a id="dronemaster.Drone.Flight.right"></a>

## right

```python
async def right(dist: int, timeout: float = 5) -> None
```

The drone flies `dist` cm to the right.

**Arguments**:

- `dist`: distance in cm in the range [20, 500]
- `timeout`: the timeout in seconds

**Raises**:

- `ProtocolError`: raised when not receiving `ok`
- `TimeoutError`: raised when not answering after `timeout`

<a id="dronemaster.Drone.Flight.clockwise"></a>

## clockwise

```python
async def clockwise(angle: int, timeout: float = 5) -> None
```

The drone rotates `angle` degrees clockwise.

**Arguments**:

- `angle`: angle in degrees in the range [1, 360]
- `timeout`: the timeout in seconds

**Raises**:

- `ProtocolError`: raised when not receiving `ok`
- `TimeoutError`: raised when not answering after `timeout`

<a id="dronemaster.Drone.Flight.counterclockwise"></a>

## counterclockwise

```python
async def counterclockwise(angle: int, timeout: float = 5) -> None
```

The drone rotates `angle` degrees counterclockwise.

**Arguments**:

- `angle`: angle in degrees in the range [1, 360]
- `timeout`: the timeout in seconds

**Raises**:

- `ProtocolError`: raised when not receiving `ok`
- `TimeoutError`: raised when not answering after `timeout`

<a id="dronemaster.Drone.Flight.land"></a>

## land

```python
async def land() -> None
```

Tries to land the drone.

**Raises**:

- `ProtocolError`: raised when not receiving `ok` (eg. the drone is not in the air)
- `TimeoutError`: raised when not answering after 20s

<a id="dronemaster.Drone.Flight.stop"></a>

## stop

```python
async def stop() -> None
```

Immediately stops the drones movement and hovers

**Raises**:

- `ProtocolError`: raised when not receiving `ok`
- `TimeoutError`: raised when not answering after 5s

<a id="dronemaster.Drone.Flight.emergency"></a>

## emergency

```python
async def emergency() -> None
```

Immediately stops all motors and lets the drone fall out of the sky

**Raises**:

- `ProtocolError`: raised when not receiving `ok`
- `TimeoutError`: raised when not answering after 5s

<a id="dronemaster.Drone.Flight.motoron"></a>

## motoron

```python
async def motoron() -> None
```

Enters motoron-mode

this is a low speed motor rotation mode to reduce the internal temperature in order to avoid overheating

**Raises**:

- `ProtocolError`: raised when not receiving `ok`
- `TimeoutError`: raised when not answering after 5s

<a id="dronemaster.Drone.Flight.motoroff"></a>

## motoroff

```python
async def motoroff() -> None
```

Exits motoron-mode

**Raises**:

- `ProtocolError`: raised when not receiving `ok`
- `TimeoutError`: raised when not answering after 5s

<a id="dronemaster.Drone.Flight.flip"></a>

## flip

```python
async def flip(direction: Literal["l", "r", "f", "b"],
               timeout: float = 5) -> None
```

Flips the drone forwards, backwards, left or right

**Arguments**:

- `direction`: the first character of the direction to flip
- `timeout`: the timeout in seconds

**Raises**:

- `ProtocolError`: raised when not receiving `ok`
- `TimeoutError`: raised when not answering after timeout

<a id="dronemaster.Drone.Flight.throwfly"></a>

## throwfly

```python
async def throwfly() -> None
```

Enables the throwfly mode.

Throw the drone within 5s horizontally to launch the drone

**Raises**:

- `ProtocolError`: raised when not receiving `ok`
- `TimeoutError`: raised when not answering after 5s

<a id="dronemaster.Drone.Flight.speed"></a>

## speed

```python
async def speed(speed: int) -> None
```

Sets the speed to use when using flying commands except the rc command

**Arguments**:

- `speed`: the speed the drone is allowed to fly in cm/s [10,100]

**Raises**:

- `ProtocolError`: raised when not receiving `ok`
- `TimeoutError`: raised when not answering after 5s

<a id="dronemaster.Drone.Flight.rc"></a>

## rc

```python
def rc(roll: int, pitch: int, throttle: int, yaw: int) -> None
```

Sends movement like you would do on a rc-controller

**Arguments**:

- `roll`: The roll (left-right) in the range [-100,100]
- `pitch`: The pitch (forwards-backwards) in the range [-100,100]
- `throttle`: The throttle (up-down) in the range [-100,100]
- `yaw`: The yaw (rotation) in the range [-100,100]

<a id="dronemaster.Drone.RGBLed"></a>

## RGBLed Objects

```python
class RGBLed(Module)
```

<a id="dronemaster.Drone.RGBLed.set"></a>

## set

```python
async def set(color: Tuple[int, int, int]) -> None
```

Sets the top-led color

**Arguments**:

- `color`: The R,G,B values in the range [0,255]

**Raises**:

- `ProtocolError`: raised when not receiving `led ok`
- `TimeoutError`: raised when not answering after 2.5s

<a id="dronemaster.Drone.RGBLed.pulse"></a>

## pulse

```python
async def pulse(color: Tuple[int, int, int], frequency: float) -> None
```

Pulses the top-led color

**Arguments**:

- `color`: The R,G,B values in the range [0,255]
- `frequency`: The frequency to pulse in Hz in range [0.1,2.5]

**Raises**:

- `ProtocolError`: raised when not receiving `led ok`
- `TimeoutError`: raised when not answering after 2.5s

<a id="dronemaster.Drone.RGBLed.flash"></a>

## flash

```python
async def flash(color1: Tuple[int, int, int], color2: Tuple[int, int, int],
                frequency: float) -> None
```

Flashes the top-led color between color1 and color2

**Arguments**:

- `color1`: The R,G,B values in the range [0,255]
- `color2`: The R,G,B values in the range [0,255]
- `frequency`: The frequency to pulse in Hz in range [0.1,10]

**Raises**:

- `ProtocolError`: raised when not receiving `led ok`
- `TimeoutError`: raised when not answering after 2.5s

<a id="dronemaster.Drone.Matrix"></a>

## Matrix Objects

```python
class Matrix(Module)
```

<a id="dronemaster.Drone.Matrix.set_brightness"></a>

## set\_brightness

```python
async def set_brightness(brightness: int) -> None
```

Sets the brigthness of the 8x8 led-matrix

**Arguments**:

- `brightness`: the brightness in the range [0,255]

**Raises**:

- `ProtocolError`: raised when not receiving `mled ok`
- `TimeoutError`: raised when not answering after 2.5s

<a id="dronemaster.Drone.Matrix.set_pattern"></a>

## set\_pattern

```python
async def set_pattern(pattern: str) -> None
```

Sets the pattern of the 8x8 led-matrix, starting at the topmost row and going to the right

**Arguments**:

- `pattern`: the pattern string, consisting of `r` for red, `b` for blue, `p` for purple, `0` for off, limited to a length of max 64

**Raises**:

- `ProtocolError`: raised when not receiving `mled ok`
- `TimeoutError`: raised when not answering after 2.5s