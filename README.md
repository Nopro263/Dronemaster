# Dronemaster
a modern alternative to the Robomaster SDK for controlling DJI Tello EDU drones.

# Api overview
This SDK only allows controlling one drone at a time. \
To get started, create a `dronemaster.Drone` object an pass it the drones ip. \
Before doing anything else, you have to call and await the drones `initialize` method to connect to the drone. \
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

# Examples
Find all examples on [GitHub](https://github.com/Nopro263/Dronemaster) in the `examples` directory.

## Simple flight
```python
...
# create the drone, but don't connect
ep_drone = dronemaster.Drone("192.168.10.1")

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
...
```

## Receiving the status
```python
...
async def printState(state: dronemaster.DroneState):
    print(state) # {'pitch': 0, 'roll': 0, 'yaw': 35, 'vgx': 0, 'vgy': 0, 'vgz': 0, 'templ': 67, 'temph': 70, 'tof': 10, 'h': 0, 'bat': 81, 'baro': 516.17, 'time': 27, 'agx': 5.0, 'agy': 4.0, 'agz': -1000.0, 'last_update': 1781868417.0927145, 'delta': 0.027984142303466797}

# create the drone, but don't connect
ep_drone = dronemaster.Drone("192.168.10.1")

# mark the drone as active and connect to it
await ep_drone.initialize()

serial = await ep_drone.serial_number()
battery = await ep_drone.battery()
print(f"Connected with drone '{serial}' with {battery}%")

ep_drone.state_subscribe(printState)

await asyncio.sleep(5)
...
```

## Receiving the video stream
```python
...
# create the drone, but don't connect
ep_drone = dronemaster.Drone("192.168.10.1")

# mark the drone as active and connect to it
await ep_drone.initialize()

serial = await ep_drone.serial_number()
battery = await ep_drone.battery()
print(f"Connected with drone '{serial}' with {battery}%")

await ep_drone.video.streamon()

# uncomment to use the downwards black and white camera
#await ep_drone.video.downvision(True)

# listen on all ips on port 11111
cap = cv2.VideoCapture("udp://0.0.0.0:11111")

while True:
    if cap.isOpened():
        ret, frame = cap.read()
        cv2.imshow('live stream', frame)
        await asyncio.sleep(1/60) # important to allow the sdk to read new commands
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

cap.release()
cv2.destroyAllWindows()

ep_drone.reboot()
...
```