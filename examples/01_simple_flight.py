__import__("sys").path += ["./src"]

import asyncio
import dronemaster

import logging
logging.basicConfig() # dronemaster uses the logging module internally

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