import asyncio
import dronemaster

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

    #await ep_drone.set_own_wifi("A926F0", "")
    await ep_drone.set_connecting_wifi("dronehub", "htl12345")

if __name__ == '__main__':
    asyncio.run(main())