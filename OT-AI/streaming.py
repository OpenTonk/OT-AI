import socket
import asyncio
import struct
import cv2
import pickle

listeners = []
sockets = []

buffer_size = 4096


async def startServer(host: str, port: int):
    socket = await asyncio.start_server(on_connection, host, port)
    await socket.serve_forever()


def addListener(cb):
    listeners.append(cb)


async def on_connection(reader, writer):
    print("client connected")

    data = b''
    p_size = struct.calcsize('L')

    while True:
        while len(data) < p_size:
            data += await reader.readexactly(buffer_size)
        packed_msg_size = data[:p_size]

        data = data[p_size:]
        msg_size = struct.unpack("L", packed_msg_size)[0]

        while len(data) < msg_size:
            data += await reader.readexactly(buffer_size)
        frame_data = data[:msg_size]
        data = data[msg_size:]

        frame = pickle.loads(frame_data)
        print(frame.size)

        cv2.imshow('frame', frame)

    cv2.destroyAllWindows()
    writer.close()
