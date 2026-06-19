__import__("sys").path += ["./src"]

import asyncio
import dronemaster

import logging
logging.basicConfig(format="%(asctime)s [%(name)s] [%(levelname)s] %(message)s") # dronemaster uses the logging module internally

async def main():
    # create the drone, but don't connect
    ep_drone = dronemaster.Drone("192.168.10.1")

    # mark the drone as active and connect to it
    await ep_drone.initialize()

    serial = await ep_drone.serial_number()
    battery = await ep_drone.battery()
    
    print(f"Connected with drone '{serial}' with {battery}%")

    ep_matrix = ep_drone.matrix

    await ep_matrix.set_brightness(255)
    await ep_matrix.set_pattern("rprp00000b")
    await asyncio.sleep(0.5)
    await ep_matrix.set_brightness(50)

    ep_led = ep_drone.rgb

    await ep_led.set((0,0,255))
    await asyncio.sleep(1)
    await ep_led.pulse((255,0,255), 2.5)
    await asyncio.sleep(0.5)
    await ep_led.flash(
        (255,0,0),
        (0,0,255),
        2
    )

    await ep_led.set((0,255,0))

    ep_drone.reboot()


if __name__ == '__main__':
    asyncio.run(main())