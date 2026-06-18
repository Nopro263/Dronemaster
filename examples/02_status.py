__import__("sys").path += ["./src"]

import asyncio
import dronemaster

import logging
logging.basicConfig(format="%(asctime)s [%(name)s] [%(levelname)s] %(message)s") # dronemaster uses the logging module internally

async def printState(state: dronemaster.DroneState):
    print(state)

async def main():
    # create the drone, but don't connect
    ep_drone = dronemaster.Drone("127.0.0.1")

    # mark the drone as active and connect to it
    await ep_drone.initialize()

    serial = await ep_drone.serial_number()
    battery = await ep_drone.battery()
    print(f"Connected with drone '{serial}' with {battery}%")

    ep_drone.state_subscribe(printState)

    await asyncio.sleep(5)
    

if __name__ == '__main__':
    asyncio.run(main())