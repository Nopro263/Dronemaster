import asyncio
import re
from typing import Callable, Coroutine, Dict, List, Optional, Any
from .utils import command_logger

OK = [r"^ok$"]
ERROR = [r"^error$"]
ANY_POSITIVE = [r"^(?!unknown command:).*?$"]
ANY = [r".*?"]

class DroneMock:
    """this class is only here so the type-checker shuts up and I don't have to export the Drone object into its own module"""
    def __init__(self) -> None:
        self.ip = ""
        self._command_counter = -1
        self._last_answer_id = b""
        self._waiting_action: Optional[Action] = None

        raise NotImplementedError("Still just a mock object")
    
    async def _on_state(self, data: dict):
        raise NotImplementedError("Nope")


class ProtocolError(Exception):
    def __init__(self, response: str):
        self.response = response
        super().__init__()

    def __str__(self):
        return f"ProtocolError({self.response})"

class Action:
    def __init__(self, command: str, positive_answers: List[str], negative_answers: List[str], drone: Any):
        self.command = command
        self.positive_answers = positive_answers
        self.negative_answers = negative_answers

        self.future = asyncio.get_running_loop().create_future()
        self.drone: DroneMock = drone

    async def send(self, transport: asyncio.DatagramTransport) -> Any:
        pass

    def on_receive(self, data: bytes, addr):
        pass

    def on_cancel(self):
        command_logger.info("cancelled while waiting for answer to '%s'", self.command)
        self.future.cancel()

class RetryAction(Action):
    """intended for commands that may be sent multiple times (eg. reads, ...)"""
    def __init__(self, command: str, positive_answers: List[str], negative_answers: List[str], timeout: float, retry_count: int, drone):
        super().__init__(command, positive_answers, negative_answers, drone)
        self.timeout = timeout
        self.retry_count = retry_count

    async def send(self, transport: asyncio.DatagramTransport):
        self.future = asyncio.get_running_loop().create_future()
        count = 1

        while count <= self.retry_count:
            command_logger.debug("[out] [retry %s/%s] [%s] '%s'", count, self.retry_count, self.drone.ip, self.command)
            transport.sendto(self.command.encode(), (self.drone.ip, 8889))

            try:
                response = await asyncio.wait_for(asyncio.shield(self.future), timeout=self.timeout)
                return response
            except asyncio.TimeoutError:
                count += 1

        command_logger.error("no answer received for '%s' from [%s]", self.command, self.drone.ip)
        raise TimeoutError("tried to send the command too often")

    def on_receive(self, data: bytes, addr):
        if data.startswith(b"Re"):
            return
        if self.future.done():
            print("?D?", data)
            return
        for pattern in self.positive_answers:
            if re.match(pattern, data.decode()):
                command_logger.info("received '%s' as answer for '%s'", data.decode(), self.command)
                self.future.set_result(data.decode())
                return

        for pattern in self.negative_answers:
            if re.match(pattern, data.decode()):
                command_logger.error("received '%s' as answer for '%s', expected one of %s", data.decode(), self.command, self.positive_answers)
                self.future.set_exception(ProtocolError(data.decode()))
                return

        print("???", data)


class RepeatAction(Action):
    """intended for commands that may not be sent multiple times (eg. takeoff, land)"""
    def __init__(self, command: str, positive_answers: List[str], negative_answers: List[str], timeout: float, drone):
        super().__init__(command, positive_answers, negative_answers, drone)
        self.timeout = timeout

    async def send(self, transport: asyncio.DatagramTransport):
        for i in range(1, 6):
            command = f"Re{self.drone._command_counter % 100:02d}{i:02d} {self.command}"
            command_logger.debug("[out] [repeat  %s] [%s] '%s'", i, self.drone.ip, command)
            transport.sendto(command.encode(), (self.drone.ip, 8889))

        self.drone._command_counter += 1

        try:
            response = await asyncio.wait_for(asyncio.shield(self.future), timeout=self.timeout)
            return response
        except asyncio.TimeoutError:
            command_logger.error("no answer received for '%s' from [%s]", self.command, self.drone.ip)
            raise TimeoutError("did not respond within " + str(self.timeout)) from None



    def on_receive(self, data: bytes, addr):
        if not data.startswith(b"Re"):
            self.handle(data)
            return

        if self.drone._last_answer_id == data[2:4]:
            return
        self.drone._last_answer_id = data[2:4]

        self.handle(data[7:])

    def handle(self, data: bytes):
        if self.future.done():
            print("?D?", data)
            return
        for pattern in self.positive_answers:
            if re.match(pattern, data.decode()):
                command_logger.info("received '%s' as answer for '%s'", data.decode(), self.command)
                self.future.set_result(data.decode())
                return

        for pattern in self.negative_answers:
            if re.match(pattern, data.decode()):
                command_logger.error("received '%s' as answer for '%s', expected one of %s", data.decode(), self.command, self.positive_answers)
                self.future.set_exception(ProtocolError(data.decode()))
                return

        print("???", data)


class RobomasterProtocol(asyncio.DatagramProtocol):
    def __init__(self):
        self.transport: asyncio.DatagramTransport = None # type: ignore
        self.drones: Dict[str, DroneMock] = {}

    def connection_made(self, transport):
        self.transport = transport

    def connection_lost(self, exc):
        self.transport = None # type: ignore

    def datagram_received(self, data, addr):
        if data.startswith(b"mid:"):
            self.state_received(data.strip(), addr)
        else:
            self.received(data.strip(), addr)

    def state_received(self, data, addr):
        INT_FIELDS = ("pitch", "roll", "yaw", "vgx", "vgy", "vgz", "bat", "templ", "temph", "tof", "h", "time")
        FLOAT_FIELDS = ("agx", "agy", "agz", "baro")

        state = {}
        for entry in data.decode().strip().split(";"):
            if not entry:
                continue
            name, value = entry.split(":")

            if name in INT_FIELDS:
                state[name] = int(value)
            elif name in FLOAT_FIELDS:
                state[name] = float(value)
            else:
                pass
        
        if addr[0] in self.drones:
            asyncio.get_running_loop().create_task(self.drones[addr[0]]._on_state(state))

    def received(self, data, addr):
        data = data.strip(b"\x00")
        if addr[0] not in self.drones:
            return
        
        drone = self.drones[addr[0]]

        if not drone._waiting_action:
            if drone._last_answer_id == data[2:4]:
                return # was from previous action
            command_logger.warning("[in] %s was not expected from [%s] since no action is running", repr(data), addr[0])
            return

        command_logger.debug("[in] [%s] %s", addr[0], repr(data))
        drone._waiting_action.on_receive(data, addr)

    async def send_action(self, action: Action, target: str):
        if target not in self.drones:
            raise RuntimeError("This target has not been registered?")
        
        drone = self.drones[target]
        if drone._waiting_action:
            drone._waiting_action.on_cancel()
            drone._waiting_action = None
        
        drone._waiting_action = action
        try:
            return await action.send(self.transport)
        finally:
            drone._waiting_action = None

    def send_command_noanswer(self, command: str, target: str):
        if target not in self.drones:
            raise RuntimeError("This target has not been registered?")
        
        command_logger.debug("[out] [no answer] [%s] '%s'", target, command)
        self.transport.sendto(command.encode(), (target, 8889))



transport: asyncio.DatagramTransport
protocol: RobomasterProtocol

async def start():
    global transport, protocol
    loop = asyncio.get_running_loop()

    reuse_port = hasattr(__import__("socket"), "SO_REUSEPORT")

    transport, protocol = await loop.create_datagram_endpoint(RobomasterProtocol, local_addr=("0.0.0.0", 8890), reuse_port=reuse_port)
    return protocol

async def stop():
    transport.close()