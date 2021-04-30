import asyncio
import logging
import time
import websockets


async def connect():
    uri = "ws://localhost:8000/ws"
    ws = await websockets.connect(uri)
    return ws

async def send(ws, payload):
    await ws.send(payload)

async def recv(ws):
    await ws.recv()

async def ping(ws):
    pong = await ws.ping()
    await pong

async def pong(ws):
    await ws.pong()

async def close(ws):
    await ws.close()

def wrapper(ws, loop, func, payload=""):
    if func == "send":
        return loop.run_until_complete(send(ws, payload))
    elif func == "recv":
        return loop.run_until_complete(recv(ws))
    elif func == "ping":
        return loop.run_until_complete(ping(ws))

def main():
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    return loop

if __name__ == "__main__":
    logger = logging.getLogger('websockets')
    logger.setLevel(logging.DEBUG)
    logger.addHandler(logging.StreamHandler())
    loop = main()
    ws = loop.run_until_complete(connect())

    try:
        s = time.time()
        while 1:
            #wrapper(ws, loop, "ping")
            wrapper(ws, loop, "send", str(round(time.time() - s)))
            wrapper(ws, loop, "recv")
            time.sleep(0.5)
            print("\n"*3)
    except KeyboardInterrupt:
        print("closing...")
        wrapper(ws, loop, "close")

    finally:
        print(time.time() - s)
