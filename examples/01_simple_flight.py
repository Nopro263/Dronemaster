__import__("sys").path += ["./src"]

import asyncio
import dronemaster

async def main():
    # create the drone, but do not connect now
    ep_drone = dronemaster.Drone("192.168.0.1")

    # mark the drone as active and connect to it
    await ep_drone.initialize()

    ep_flight = ep_drone.flight

    # takeoff and wait for completion (up to 20s)
    await ep_flight.takeoff()

    # fly forwards 20cm
    await ep_flight.forward(20, timeout=7)

    # land again
    await ep_flight.land()

if __name__ == '__main__':
    asyncio.run(main())