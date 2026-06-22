import asyncio
import dronemaster

import logging
logging.basicConfig(format="%(asctime)s [%(name)s] [%(levelname)s] %(message)s") # dronemaster uses the logging module internally

async def main():
    # create the drone, but don't connect
    ep_drone = dronemaster.Drone("127.0.0.1")

    # mark the drone as active and connect to it
    await ep_drone.initialize()

    ep_flight = ep_drone.flight

    try:
        # motoroff
        await ep_flight.motoroff()
    except dronemaster.ProtocolError:
        pass
    await asyncio.sleep(1)
    # motoron
    await ep_flight.motoron()
    await asyncio.sleep(1)
    # motoroff
    await ep_flight.motoroff()
    await asyncio.sleep(1)

    # takeoff and wait for completion (up to 20s)
    await ep_flight.takeoff()

    serial = await ep_drone.serial_number()
    battery = await ep_drone.battery()
    height = await ep_drone.tof()
    dist = await ep_drone.ext_tof()
    
    print(f"Connected with drone '{serial}' with {battery}%")
    print(f"H:{height} D:{dist}")

    # fly forwards 20cm
    await ep_flight.forward(20, timeout=7)
    # fly left 20cm
    await ep_flight.left(20, timeout=7)
    # fly right 20cm
    await ep_flight.right(20, timeout=7)
    # fly backwards 20cm
    await ep_flight.back(20, timeout=7)

    # fly up 20cm
    await ep_flight.up(20, timeout=7)
    # fly down 20cm
    await ep_flight.down(20, timeout=7)

    await ep_flight.clockwise(45, timeout=10)
    await ep_flight.counterclockwise(45, timeout=10)

    # land again
    await ep_flight.land()

if __name__ == '__main__':
    asyncio.run(main())