import asyncio
import dronemaster
import cv2

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

    await ep_drone.video.set_video_port(11112) # per default, port 11111 is used

    await ep_drone.video.streamon()

    # uncomment to use the downwards black and white camera
    #await ep_drone.video.downvision(True)

    # listen on all ips on port 11112
    # the drone sends the video in H264 format with an I-Frame every few seconds
    cap = cv2.VideoCapture("udp://0.0.0.0:11112")

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