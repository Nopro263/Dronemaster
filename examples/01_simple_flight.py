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