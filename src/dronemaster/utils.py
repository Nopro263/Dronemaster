import logging

def limit(v: float, min: float, max: float):
    if v > max or v < min:
        raise ValueError(f"{v} must be in range of [{min},{max}]")

command_logger = logging.getLogger("dronemaster_commands")
command_logger.setLevel(logging.DEBUG)