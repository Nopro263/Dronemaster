import asyncio
import sys
from . import ProtocolSimulator

async def main():
    ip = "0.0.0.0"
    if len(sys.argv) == 2:
        ip = sys.argv[1]
    
    simulator = ProtocolSimulator(ip=ip)
    await simulator.loop()

if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("Exiting")
        exit(0)