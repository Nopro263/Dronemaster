import asyncio
import dronemaster
import cv2

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
    

if __name__ == '__main__':
    asyncio.run(main())