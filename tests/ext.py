import asyncio
import dronemaster

import logging
logging.basicConfig(format="%(asctime)s [%(name)s] [%(levelname)s] %(message)s") # dronemaster uses the logging module internally
dronemaster.command_logger.setLevel(logging.INFO)

async def main():
    # create the drone, but don't connect
    ep_drone = dronemaster.Drone("127.0.0.1")

    # mark the drone as active and connect to it
    await ep_drone.initialize()

    serial = await ep_drone.serial_number()
    battery = await ep_drone.battery()
    hardware = await ep_drone.get_hardware()
    flight_time = await ep_drone.flight_time()
    sdk = await ep_drone.sdk_version()
    wifi_serial = await ep_drone.wifi_serial()
    wifi_version = await ep_drone.wifi_version()
    
    print(f"Connected with drone '{serial}' with {battery}%")
    print(f"Hardware:{hardware} Flight-Time:{flight_time}s SDK:{sdk}")
    print(f"Wifi SN:{wifi_serial} Version:{wifi_version}")

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