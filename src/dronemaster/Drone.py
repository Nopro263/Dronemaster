import inspect

from .low_level import ProtocolError, RepeatAction, RetryAction, RobomasterProtocol, Action, OK, ANY
from . import low_level as l
from .utils import limit
from time import time
from typing import Dict, TypedDict, Any, Optional, Tuple, Callable, Coroutine, Literal, Union

class DroneState(TypedDict):
    pitch: int
    """pitch in degrees"""
    roll: int
    """roll in degrees"""
    yaw: int
    """yaw in degrees"""

    vgx: int
    """velocity in x-direction (forwards/backwards) in dm/s"""
    vgy: int
    """velocity in y-direction (left/right) in dm/s"""
    vgz: int
    """velocity in z-direction (up/down) in dm/s"""

    bat: int
    """battery percentage"""
    templ: int
    """the lower range of the internal temperature sensor in °C"""
    temph: int
    """the upper range of the internal temperature sensor in °C"""

    tof: int
    """the vertical distance to ground in cm. reported as 10 if out of range"""

    h: int
    """the calculated height, note that this only works in flight"""

    time: int
    """number of seconds the drone has been flying"""

    agx: float
    """acceleration in x-direction in cm/s²"""
    agy: float
    """acceleration in y-direction in cm/s²"""
    agz: float
    """acceleration in z-direction in cm/s²"""

    baro: float
    """Height above sea level as reported by the barometer in m"""

    last_update: float
    """unix timestamp of the last update"""

    delta: float
    """time in seconds between the last two state packets"""


class Drone:
    def __init__(self, ip: str):
        self.ip = ip
        self.flight = Flight(self)
        self.rgb = RGBLed(self)
        self.matrix = Matrix(self)
        self.video = Video(self)
        self.last_state: Dict[str, Any] = {}
        self.connected = False
        self._state_subscribers = []

    async def action(self, action: Action, ignore_not_connected: bool = False) -> Any:
        if not self.connected and not ignore_not_connected:
            raise ProtocolError("you are not connected to the drone")
        return await l.protocol.send_action(action, self.ip)

    async def _on_state(self, state: dict):
        if "last_update" in self.last_state:
            delta = time() - self.last_state["last_update"]
        else:
            delta = 0
        state.update({"last_update": time(), "delta": delta})
        self.last_state = state
        for sub in self._state_subscribers:
            r = sub(state)
            if inspect.iscoroutine(r):
                await r

    def state_subscribe(self, callable: Callable[[DroneState], Coroutine[Any, Any, None]]):
        self._state_subscribers.append(callable)

    async def initialize(self) -> None:
        """
        Initializes the drone connection and optionally starts the communication channel.
        This function must be called before any other

        :raises ProtocolError: raised when not receiving `ok`
        :raises TimeoutError: raised when not answering after 2.5s
        """

        if not hasattr(l, "transport"):
            await l.start()
        
        if l.protocol.on_state != l.protocol._on_state:
            raise RuntimeError("the current sdk supports only one connected drone at a time")
        
        await self.action(RetryAction(
            command="command",
            positive_answers=OK,
            negative_answers=ANY,
            retry_count=5,
            timeout=0.5
        ), ignore_not_connected=True)

        l.protocol.on_state = self._on_state
        self.connected = True

    async def serial_number(self) -> str:
        """
        Queries the drone for its serial number in the format `[A-Z0-9]{14}`

        :returns: the serial number in the format `[A-Z0-9]{14}`
        :raises ProtocolError: raised when not receiving the correct format
        :raises TimeoutError: raised when not answering after 5s
        """
        return await self.action(RetryAction(
            command="sn?",
            positive_answers=[r"^[A-Z0-9]{14}$"],
            negative_answers=ANY,
            retry_count=5,
            timeout=1
        ))

    async def battery(self) -> int:
        """
        Queries the drone for its current battery charce percentage from 0-100

        :returns: the battery percentage
        :raises ProtocolError: raised when not receiving the battery percentage
        :raises TimeoutError: raised when not answering after 5s
        """
        return int(await self.action(RetryAction(
            command="battery?",
            positive_answers=[r"^\d{1,3}$"],
            negative_answers=ANY,
            retry_count=5,
            timeout=1
        )))

    async def ext_tof(self):
        """
        Reads the horizontal distance of the drone to the front.

        :returns: the horizontal distance to the front in mm or `None` if out of range
        :raises ProtocolError: raised when not receiving data in the correct format
        :raises TimeoutError: raised when not answering after 2.5s
        """
        raw = await self.action(RetryAction(
            command="EXT tof?",
            positive_answers=[r"^tof \d+$"],
            negative_answers=ANY,
            retry_count=5,
            timeout=1
        ))
        tof = int(raw.split(" ")[1])

        if tof == 8190:
            return None
        else:
            return tof

    async def tof(self) -> Optional[int]:
        """
        Reads the vertical distance of the drone to ground.

        :returns: the vertical distance to ground in mm or `None` if out of range
        :raises ProtocolError: raised when not receiving data in the correct format
        :raises TimeoutError: raised when not answering after 2.5s
        """
        raw = await self.action(RetryAction(
            command="tof?",
            positive_answers=[r"^\d+mm$"],
            negative_answers=ANY,
            retry_count=5,
            timeout=1
        ))
        tof = int(raw[:-2])

        if tof == 100:
            return None
        else:
            return tof

    async def keepalive(self) -> bool:
        """
        Sends a "ping" packet to the drone to stop it from landing automatically, but only if there is no currently waiting command

        :returns: True when the ping was successful, False when it was skipped
        :raises ProtocolError: raised when not receiving `ok`
        :raises TimeoutError: raised when not answering after 2.5s
        """
        if l.protocol.waiting_action is None:
            await self.action(RetryAction(
                command="command",
                positive_answers=OK,
                negative_answers=ANY,
                retry_count=5,
                timeout=0.5
            ))
            return True
        return False

    async def send_raw_command(self, command, wait_for_answer: bool = True, timeout: float = 1) -> Optional[str]:
        """
        Sends a raw command to the drone. Intended for debugging/manual mode

        :param wait_for_answer: if the code expects an answer
        :param timeout: when expecting an answer, how long to wait 
        :returns: the answer or `None` if no answer is expected
        :raises ProtocolError: should never happen
        :raises TimeoutError: raised when not answering after 5 * timeout
        """
        if wait_for_answer:
            return await self.action(RetryAction(
                command=command,
                positive_answers=ANY,
                negative_answers=ANY,
                retry_count=5,
                timeout=timeout
            ))
        else:
            l.protocol.send_command_noanswer(command, self.ip)
            return None

    def reboot(self) -> None:
        """
        Reboots the drone
        """
        l.protocol.send_command_noanswer("reboot", self.ip)
        self.connected = False
        l.protocol.on_state = l.protocol._on_state

class Module:
    def __init__(self, drone: Drone):
        self.drone = drone

    async def action(self, action: Action):
        return await self.drone.action(action)

class Video(Module):
    async def streamon(self) -> None:
        """
        Starts the stream so the drone sends the H264 stream to port 11111

        :raises ProtocolError: raised when not receiving `ok`
        :raises TimeoutError: raised when not answering after 5s
        """
        await self.action(RetryAction(
            command="streamon",
            positive_answers=OK,
            negative_answers=ANY,
            retry_count=5,
            timeout=1
        ))

    async def streamoff(self) -> None:
        """
        Stops the video stream

        :raises ProtocolError: raised when not receiving `ok`
        :raises TimeoutError: raised when not answering after 5s
        """
        await self.action(RetryAction(
            command="streamoff",
            positive_answers=OK,
            negative_answers=ANY,
            retry_count=5,
            timeout=1
        ))
    
    async def downvision(self, on: bool) -> None:
        """
        Switches the used camera.

        :param on: if the downwards camera should be used
        :raises ProtocolError: raised when not receiving `ok`
        :raises TimeoutError: raised when not answering after 5s
        """
        await self.action(RetryAction(
            command=f"downvision {1 if on else 0}",
            positive_answers=OK,
            negative_answers=ANY,
            retry_count=5,
            timeout=1
        ))
    
    async def setfps(self, fps: Literal["high","middle","low"]) -> None:
        """
        Sets the streams fps to
        - `high` -> 30fps
        - `middle` -> 15fps
        - `low` -> 5fps

        :param fps: the requested fps
        :raises ProtocolError: raised when not receiving `ok`
        :raises TimeoutError: raised when not answering after 5s
        """
        await self.action(RetryAction(
            command=f"setfps {fps}",
            positive_answers=OK,
            negative_answers=ANY,
            retry_count=5,
            timeout=1
        ))
    
    async def setbitrate(self, bitrate: Literal["auto",1,2,3,4,5]) -> None:
        """
        Sets the streams maximum bitrate to auto or the requested Mbps

        :param bitrate: the bitrate in Mbps or `auto`
        :raises ProtocolError: raised when not receiving `ok`
        :raises TimeoutError: raised when not answering after 5s
        """
        bt = 0

        if bitrate == "auto":
            bt = 0
        else:
            bt = bitrate

        await self.action(RetryAction(
            command=f"setbitrate {bt}",
            positive_answers=OK,
            negative_answers=ANY,
            retry_count=5,
            timeout=1
        ))
    
    async def setresolution(self, resolution: Literal["high","low"]) -> None:
        """
        Sets the video streams resolution
        - `high` -> 720P
        - `low` -> 480P

        :param resolution: the requested resolution
        :raises ProtocolError: raised when not receiving `ok`
        :raises TimeoutError: raised when not answering after 5s
        """

        await self.action(RetryAction(
            command=f"setresolution {resolution}",
            positive_answers=OK,
            negative_answers=ANY,
            retry_count=5,
            timeout=1
        ))

class Flight(Module):
    async def takeoff(self) -> None:
        """
        Tries to takeoff

        :raises ProtocolError: raised when not receiving `ok`
        :raises TimeoutError: raised when not answering after 20s
        """
        await self.action(RepeatAction(
            command="takeoff",
            positive_answers=OK,
            negative_answers=ANY,
            timeout=20
        ))

    async def forward(self, dist: int, timeout: float = 5) -> None:
        """
        The drone flies `dist` cm forwards.

        :param dist: distance in cm in the range [20, 500]
        :param timeout: the timeout in seconds
        :raises ProtocolError: raised when not receiving `ok`
        :raises TimeoutError: raised when not answering after `timeout`
        """
        limit(dist, 20, 500)
        await self.action(RepeatAction(
            command=f"forward {dist}",
            positive_answers=OK,
            negative_answers=ANY,
            timeout=timeout
        ))

    async def back(self, dist: int, timeout: float = 5) -> None:
        """
        The drone flies `dist` cm backwards.

        :param dist: distance in cm in the range [20, 500]
        :param timeout: the timeout in seconds
        :raises ProtocolError: raised when not receiving `ok`
        :raises TimeoutError: raised when not answering after `timeout`
        """
        limit(dist, 20, 500)
        await self.action(RepeatAction(
            command=f"back {dist}",
            positive_answers=OK,
            negative_answers=ANY,
            timeout=timeout
        ))

    async def up(self, dist: int, timeout: float = 5) -> None:
        """
        The drone flies `dist` cm upwards.

        :param dist: distance in cm in the range [20, 500]
        :param timeout: the timeout in seconds
        :raises ProtocolError: raised when not receiving `ok`
        :raises TimeoutError: raised when not answering after `timeout`
        """
        limit(dist, 20, 500)
        await self.action(RepeatAction(
            command=f"up {dist}",
            positive_answers=OK,
            negative_answers=ANY,
            timeout=timeout
        ))

    async def down(self, dist: int, timeout: float = 5) -> None:
        """
        The drone flies `dist` cm downwards.

        :param dist: distance in cm in the range [20, 500]
        :param timeout: the timeout in seconds
        :raises ProtocolError: raised when not receiving `ok`
        :raises TimeoutError: raised when not answering after `timeout`
        """
        limit(dist, 20, 500)
        await self.action(RepeatAction(
            command=f"down {dist}",
            positive_answers=OK,
            negative_answers=ANY,
            timeout=timeout
        ))

    async def left(self, dist: int, timeout: float = 5) -> None:
        """
        The drone flies `dist` cm to the left.

        :param dist: distance in cm in the range [20, 500]
        :param timeout: the timeout in seconds
        :raises ProtocolError: raised when not receiving `ok`
        :raises TimeoutError: raised when not answering after `timeout`
        """
        limit(dist, 20, 500)
        await self.action(RepeatAction(
            command=f"left {dist}",
            positive_answers=OK,
            negative_answers=ANY,
            timeout=timeout
        ))

    async def right(self, dist: int, timeout: float = 5) -> None:
        """
        The drone flies `dist` cm to the right.

        :param dist: distance in cm in the range [20, 500]
        :param timeout: the timeout in seconds
        :raises ProtocolError: raised when not receiving `ok`
        :raises TimeoutError: raised when not answering after `timeout`
        """
        limit(dist, 20, 500)
        await self.action(RepeatAction(
            command=f"right {dist}",
            positive_answers=OK,
            negative_answers=ANY,
            timeout=timeout
        ))

    async def clockwise(self, angle: int, timeout: float = 5) -> None:
        """
        The drone rotates `angle` degrees clockwise.

        :param angle: angle in degrees in the range [1, 360]
        :param timeout: the timeout in seconds
        :raises ProtocolError: raised when not receiving `ok`
        :raises TimeoutError: raised when not answering after `timeout`
        """
        limit(angle, 1, 360)
        await self.action(RepeatAction(
            command=f"cw {angle}",
            positive_answers=OK,
            negative_answers=ANY,
            timeout=timeout
        ))

    async def counterclockwise(self, angle: int, timeout: float = 5) -> None:
        """
        The drone rotates `angle` degrees counterclockwise.

        :param angle: angle in degrees in the range [1, 360]
        :param timeout: the timeout in seconds
        :raises ProtocolError: raised when not receiving `ok`
        :raises TimeoutError: raised when not answering after `timeout`
        """
        limit(angle, 1, 360)
        await self.action(RepeatAction(
            command=f"ccw {angle}",
            positive_answers=OK,
            negative_answers=ANY,
            timeout=timeout
        ))

    async def land(self) -> None:
        """
        Tries to land the drone.

        :raises ProtocolError: raised when not receiving `ok` (eg. the drone is not in the air)
        :raises TimeoutError: raised when not answering after 20s
        """
        await self.action(RepeatAction(
            command="land",
            positive_answers=OK,
            negative_answers=ANY,
            timeout=20
        ))

    async def stop(self) -> None:
        """
        Immediately stops the drones movement and hovers

        :raises ProtocolError: raised when not receiving `ok`
        :raises TimeoutError: raised when not answering after 5s
        """
        await self.action(RepeatAction(
            command="stop",
            positive_answers= [r"^forced stop$", r"^ok$"],
            negative_answers=ANY,
            timeout=5
        ))

    async def emergency(self) -> None:
        """
        Immediately stops all motors and lets the drone fall out of the sky

        :raises ProtocolError: raised when not receiving `ok`
        :raises TimeoutError: raised when not answering after 5s
        """
        await self.action(RetryAction(
            command="emergency",
            positive_answers=OK,
            negative_answers=ANY,
            retry_count=5,
            timeout=1
        ))

    async def motoron(self) -> None:
        """
        Enters motoron-mode.
        this is a low speed motor rotation mode to reduce the internal temperature in order to avoid overheating

        :raises ProtocolError: raised when not receiving `ok`
        :raises TimeoutError: raised when not answering after 5s
        """
        await self.action(RetryAction(
            command="motoron",
            positive_answers=OK,
            negative_answers=ANY,
            retry_count=5,
            timeout=1
        ))

    async def motoroff(self) -> None:
        """
        Exits motoron-mode

        :raises ProtocolError: raised when not receiving `ok`
        :raises TimeoutError: raised when not answering after 5s
        """
        await self.action(RetryAction(
            command="motoroff",
            positive_answers=OK,
            negative_answers=ANY,
            retry_count=5,
            timeout=1
        ))

    async def flip(self, direction: Literal["l", "r", "f", "b"], timeout: float = 5) -> None:
        """
        Flips the drone forwards, backwards, left or right

        :param direction: the first character of the direction to flip
        :param timeout: the timeout in seconds
        :raises ProtocolError: raised when not receiving `ok`
        :raises TimeoutError: raised when not answering after timeout
        """
        if direction not in ("l", "r", "f", "b"):
            raise ValueError("Direction must be in l,r,f,b")

        await self.action(RepeatAction(
            command=f"flip {direction}",
            positive_answers=OK,
            negative_answers=ANY,
            timeout=timeout
        ))

    def rc(self, roll: int, pitch: int, throttle: int, yaw: int) -> None:
        """
        Sends movement like you would do on a rc-controller

        :param roll: The roll (left-right) in the range [-100,100]
        :param pitch: The pitch (forwards-backwards) in the range [-100,100]
        :param throttle: The throttle (up-down) in the range [-100,100]
        :param yaw: The yaw (rotation) in the range [-100,100]
        """
        limit(roll, -100, 100)
        limit(pitch, -100, 100)
        limit(throttle, -100, 100)
        limit(yaw, -100, 100)

        l.protocol.send_command_noanswer(f"rc {roll} {pitch} {throttle} {yaw}", self.drone.ip)

class RGBLed(Module):
    async def set(self, color: Tuple[int, int, int]) -> None:
        """
        Sets the top-led color

        :param color: The R,G,B values in the range [0,255]
        :raises ProtocolError: raised when not receiving `led ok`
        :raises TimeoutError: raised when not answering after 2.5s
        """
        red, green, blue = color
        limit(red, 0, 255)
        limit(green, 0, 255)
        limit(blue, 0, 255)
        await self.action(RetryAction(
            command=f"EXT led {red} {green} {blue}",
            positive_answers=[r"^led ok$"],
            negative_answers=ANY,
            timeout=0.5,
            retry_count=5
        ))

    async def pulse(self, color: Tuple[int, int, int], frequency: float) -> None:
        """
        Pulses the top-led color

        :param color: The R,G,B values in the range [0,255]
        :param frequency: The frequency to pulse in Hz in range [0.1,2.5]
        :raises ProtocolError: raised when not receiving `led ok`
        :raises TimeoutError: raised when not answering after 2.5s
        """
        red, green, blue = color
        limit(red, 0, 255)
        limit(green, 0, 255)
        limit(blue, 0, 255)
        limit(frequency, 0.1, 2.5)
        await self.action(RetryAction(
            command=f"EXT led br {frequency} {red} {green} {blue}",
            positive_answers=[r"^led ok$"],
            negative_answers=ANY,
            timeout=0.5,
            retry_count=5
        ))

    async def flash(self, color1: Tuple[int, int, int], color2: Tuple[int, int, int], frequency: float) -> None:
        """
        Flashes the top-led color between color1 and color2

        :param color1: The R,G,B values in the range [0,255]
        :param color2: The R,G,B values in the range [0,255]
        :param frequency: The frequency to pulse in Hz in range [0.1,10]
        :raises ProtocolError: raised when not receiving `led ok`
        :raises TimeoutError: raised when not answering after 2.5s
        """
        red1, green1, blue1 = color1
        red2, green2, blue2 = color2
        limit(red1, 0, 255)
        limit(green1, 0, 255)
        limit(blue1, 0, 255)
        limit(red2, 0, 255)
        limit(green2, 0, 255)
        limit(blue2, 0, 255)
        limit(frequency, 0.1, 10)
        await self.action(RetryAction(
            command=f"EXT led bl {frequency} {red1} {green1} {blue1} {red2} {green2} {blue2}",
            positive_answers=[r"^led ok$"],
            negative_answers=ANY,
            timeout=0.5,
            retry_count=5
        ))

class Matrix(Module):
    def __init__(self, drone: Drone):
        super().__init__(drone)
        self.pattern = "ppppp000"\
                       "00p00000"\
                       "00pbbbbb"\
                       "00p00b00"\
                       "00p00b00"\
                       "00000b00"\
                       "00000b00"\
                       "rrrrpppp"

    async def set_brightness(self, brightness: int) -> None:
        """
        Sets the brigthness of the 8x8 led-matrix

        :param brightness: the brightness in the range [0,255]
        :raises ProtocolError: raised when not receiving `mled ok`
        :raises TimeoutError: raised when not answering after 2.5s
        """
        limit(brightness, 0, 255)
        await self.action(RetryAction(
            command=f"EXT mled sl {brightness}",
            positive_answers=[r"^matrix ok$"],
            negative_answers=ANY,
            timeout=0.5,
            retry_count=5
        ))

    async def set_pattern(self, pattern: str) -> None:
        """
        Sets the pattern of the 8x8 led-matrix, starting at the topmost row and going to the right

        :param pattern: the pattern string, consisting of `r` for red, `b` for blue, `p` for purple, `0` for off, limited to a length of max 64
        :raises ProtocolError: raised when not receiving `mled ok`
        :raises TimeoutError: raised when not answering after 2.5s
        """
        limit(len(pattern.replace("r","").replace("b","").replace("p","").replace("0","")), 0, 0)
        limit(len(pattern), 1, 64)

        await self.action(RetryAction(
            command=f"EXT mled g {pattern}",
            positive_answers=[r"^matrix ok$"],
            negative_answers=ANY,
            timeout=0.5,
            retry_count=5
        ))

        self.pattern = pattern