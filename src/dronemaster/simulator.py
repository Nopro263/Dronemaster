import asyncio
from typing import Any, Optional
import re
import cv2

class SimulatorProtocol(asyncio.DatagramProtocol):
    def __init__(self) -> None:
        super().__init__()
        self.SERIAL = "0TQZM7NCNT0HAY"
        self.HARDWARE = "RMTT"
        self.SDK = 30
        self.WIFIVERSION = "wifiv9.9.9.9"

        self.connected = set()
        self.motoron = False
        self.air_time = 0
        self.battery = 100
        self.tof = 10
        
        self.ext_tof = 8190

        self.video = False
        self.video_port = 11111
        self.cap: cv2.VideoCapture = None # type: ignore

        self.handled = {}
    
    def handle_command(self, command: str, addr: tuple[str | Any, int]) -> Optional[str]:
        if command == "command":
            self.connected.add(addr[0])
            return "ok"
        
        if not self.connected:
            return None
    
        if command == "motoron":
            if self.motoron:
                return "error"
            else:
                self.motoron = True
                return "ok"
        
        if command == "motoroff":
            if not self.motoron:
                return "error"
            else:
                self.motoron = False
                return "ok"
        
        if command == "takeoff":
            if self.air_time != 0:
                return "error"
            else:
                self.air_time = 1
                return "ok"
        
        if command == "land":
            if self.air_time == 0:
                return "error"
            else:
                self.air_time = 0
                return "ok"
        
        if command == "stop":
            if self.air_time == 0:
                return "error"
            else:
                return "ok"
            
        if command == "streamon":
            self.video = True
            self.cap = cv2.VideoCapture(0)
            return "ok"
    
        if command == "streamoff":
            self.video = False
            self.cap.release()
            return "ok"
        
        
        if m := re.match(r"forward (\d+)$", command):
            if self.air_time == 0:
                return "error"
            else:
                dist = m.group(1)
                print("forward", dist)
                return "ok"
        
        if m := re.match(r"back (\d+)$", command):
            if self.air_time == 0:
                return "error"
            else:
                dist = m.group(1)
                print("backwards", dist)
                return "ok"
        
        if m := re.match(r"left (\d+)$", command):
            if self.air_time == 0:
                return "error"
            else:
                dist = m.group(1)
                print("left", dist)
                return "ok"
        
        if m := re.match(r"right (\d+)$", command):
            if self.air_time == 0:
                return "error"
            else:
                dist = m.group(1)
                print("right", dist)
                return "ok"
        
        if m := re.match(r"up (\d+)$", command):
            if self.air_time == 0:
                return "error"
            else:
                dist = m.group(1)
                print("up", dist)
                return "ok"
        
        if m := re.match(r"down (\d+)$", command):
            if self.air_time == 0:
                return "error"
            else:
                dist = m.group(1)
                print("down", dist)
                return "ok"
        
        if m := re.match(r"cw (\d+)$", command):
            if self.air_time == 0:
                return "error"
            else:
                deg = m.group(1)
                print("clockwise", deg)
                return "ok"
        
        if m := re.match(r"ccw (\d+)$", command):
            if self.air_time == 0:
                return "error"
            else:
                deg = m.group(1)
                print("counter-clockwise", deg)
                return "ok"
        
        if m := re.match(r"port (\d+) (\d+)$", command):
            print("Video port is now:", m.group(2))
            self.video_port = int(m.group(2))
            return "ok"
        
        if m := re.match(r"ap (.+) (.+)$", command):
            print("connecting to wifi", m.group(1), m.group(2))
            self.transport.close()
            return "OK,drone will reboot in 3s\x00"
        
        if m := re.match(r"wifi (.+) (.*)$", command):
            print("setting own wifi to", m.group(1), m.group(2))
            self.transport.close()
            return "OK,drone will reboot in 3s\x00"
        
        if command == "sn?":
            return self.SERIAL
    
        if command == "hardware?":
            return self.HARDWARE

        if command == "battery?":
            return str(self.battery)
        
        if command == "time?":
            return f"{self.air_time}s"
        
        if command == "sdk?":
            return str(self.SDK)
        
        if command == "wifi?":
            return "SN???"
        
        if command == "wifiversion?":
            return self.WIFIVERSION
    
        if command == "throwfly":
            print("The simulator can not be thrown :(")
            return "ok"
    
        if command == "tof?":
            return f"{self.tof}mm"
    
        if command == "EXT tof?":
            return f"tof {self.ext_tof}"
        
        if command == "reboot":
            self.transport.close()
            return None
        
        if m := re.match(r"rc (-?\d+) (-?\d+) (-?\d+) (-?\d+)$", command):
            roll, pitch, throttle, yaw = m.group(1), m.group(2), m.group(3), m.group(4)
            print(f"R:{roll} P:{pitch} T:{throttle} Y:{yaw}")
            return None
        
        if m := re.match(r"EXT mled sl (\d+)$", command):
            brightness = m.group(1)
            print("brightness", brightness)
            return "matrix ok"
        
        if m := re.match(r"EXT mled g ([rbp0]{1,64})$", command):
            pattern = m.group(1)
            print("static pattern", pattern)
            return "matrix ok"

        if m := re.match(r"EXT led (\d+) (\d+) (\d+)$", command):
            r, g, b = m.group(1), m.group(2), m.group(3)
            print("led", r, g, b)
            return "led ok"
        
        if m := re.match(r"EXT led br (\d+\.?\d*) (\d+) (\d+) (\d+)$", command):
            t, r, g, b = m.group(1), m.group(2), m.group(3), m.group(4)
            print("led-pulse", t, r, g, b)
            return "led ok"
        
        if m := re.match(r"EXT led bl (\d+\.?\d*) (\d+) (\d+) (\d+) (\d+) (\d+) (\d+)$", command):
            t, r1, g1, b1, r2, g2, b2 = m.group(1), m.group(2), m.group(3), m.group(4), m.group(5), m.group(6), m.group(7)
            print("led-flash", t, (r1, g1, b1), (r2, g2, b2))
            return "led ok"

        print("Data from", addr, command)
        return f"unknown command: {command}"
    
    def send_status(self):
        pitch = 0
        roll = 0
        yaw = 0
        vgx = 0
        vgy = 0
        vgz = 0
        templ = 0
        temph = 0
        height = 0
        baro = 0
        agx = 0
        agy = 0
        agz = 0

        state_payload = (
                f"mid:-1;x:-1;y:-1;z:-1;mpry:0,0,0;"
                f"pitch:{pitch};roll:{roll};yaw:{yaw};"
                f"vgx:{vgx};vgy:{vgy};vgz:{vgz};"
                f"templ:{templ};temph:{temph};"
                f"tof:{self.tof};h:{height};bat:{self.battery};"
                f"baro:{baro:.2f};time:{self.air_time};"
                f"agx:{agx:.2f};agy:{agy:.2f};agz:{agz:.2f};\r\n"
            )
        
        for client in self.connected:
            self.transport.sendto(state_payload.encode(), (client, 8890))
    
    def send_video(self):
        if self.video and self.cap:
            ret, frame = self.cap.read()
            if not ret:
                return
            frame = cv2.resize(frame, (480, 360))
            ret, encoded_img = cv2.imencode('.jpg', frame, [cv2.IMWRITE_JPEG_QUALITY, 50])
            if ret:
                data = encoded_img.tobytes()

                for client in self.connected:
                    self.transport.sendto(data, (client, self.video_port))


    def datagram_received(self, data: bytes, addr: tuple[str | Any, int]) -> None:
        m = re.match(r"Re(\d{2})(\d{2}) (.*?)$", data.decode())
        if m:
            cmdid, cmdrepeat, cmd = m.group(1), m.group(2), m.group(3)

            if cmdid not in self.handled:
                response = self.handle_command(cmd, addr)
                self.handled[cmdid] = response
            
            if self.handled[cmdid] is not None:
                self.transport.sendto(f"Re{cmdid}{cmdrepeat} {self.handled[cmdid]}".encode(), addr)
            return
        else:
            response = self.handle_command(data.decode(), addr)
            if response is not None:
                self.transport.sendto(response.encode(), addr)
            return

    def connection_lost(self, exc: Exception | None) -> None:
        return super().connection_lost(exc)
    
    def connection_made(self, transport: asyncio.DatagramTransport) -> None:
        self.transport = transport
        return super().connection_made(transport)
    
    def error_received(self, exc: Exception) -> None:
        return super().error_received(exc)
    

class ProtocolSimulator:
    async def start(self) -> SimulatorProtocol:
        loop = asyncio.get_event_loop()

        reuse_port = hasattr(__import__("socket"), "SO_REUSEPORT")

        transport, protocol = await loop.create_datagram_endpoint(SimulatorProtocol, local_addr=("0.0.0.0", 8889), reuse_port=reuse_port)

        async def status():
            while not transport.is_closing():
                protocol.send_status()
                await asyncio.sleep(1/10)
        
        async def video():
            while not transport.is_closing():
                protocol.send_video()
                await asyncio.sleep(1/30)
        
        loop.create_task(status())
        loop.create_task(video())

        return protocol
    
    async def loop(self):
        print("Starting simulator on '127.0.0.1'")
        protocol = await self.start()
        while True:
            if protocol.transport.is_closing():
                print("Rebooting")
                await asyncio.sleep(5)
                protocol = await self.start()
            await asyncio.sleep(5)