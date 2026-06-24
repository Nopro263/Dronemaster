import asyncio
from .import ProtocolSimulator

async def main():
    simulator = ProtocolSimulator()
    await simulator.loop()

if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("Exiting")
        exit(0)