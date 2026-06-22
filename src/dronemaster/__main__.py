import asyncio
from .import ProtocolSimulator

async def main():
    simulator = ProtocolSimulator()
    await simulator.loop()

if __name__ == '__main__':
    asyncio.run(main())