import asyncio
import dronemaster

import logging
logging.basicConfig(format="%(asctime)s [%(name)s] [%(levelname)s] %(message)s") # dronemaster uses the logging module internally
dronemaster.command_logger.setLevel(logging.INFO) # do not log raw commands

async def main():
    # create the drone, but don't connect
    ep_drone_1 = dronemaster.Drone("127.0.0.1")
    ep_drone_2 = dronemaster.Drone("127.0.0.2")

    # mark the drone as active and connect to it
    await ep_drone_1.initialize()
    await ep_drone_2.initialize()

    serial = await ep_drone_1.serial_number()
    battery = await ep_drone_1.battery()
    print(f"Drone 1: '{serial}' with {battery}%")

    serial = await ep_drone_2.serial_number()
    battery = await ep_drone_2.battery()
    print(f"Drone 2: '{serial}' with {battery}%")


    await asyncio.gather( # run multiple tasks parallel
        ep_drone_1.flight.takeoff(),
        ep_drone_2.flight.takeoff()
    )

    await asyncio.gather(
        ep_drone_1.flight.left(50, timeout=5),
        ep_drone_2.flight.right(50, timeout=5)
    )

    await asyncio.gather(
        ep_drone_1.flight.land(),
        ep_drone_2.flight.land()
    )

    await asyncio.sleep(1)

    print(ep_drone_1.last_state)
    print(ep_drone_2.last_state)

if __name__ == '__main__':
    asyncio.run(main())