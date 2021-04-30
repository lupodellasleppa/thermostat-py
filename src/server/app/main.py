import json
import logging
import os
from typing import List

from fastapi import (
    FastAPI, Response, status, WebSocket, WebSocketDisconnect
)
from fastapi.middleware.cors import CORSMiddleware


class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)

    async def send_personal_message(self, message: str, websocket: WebSocket):
        await websocket.send_text(message)

    async def broadcast(self, message):
        for connection in self.active_connections:
            await connection.send_text(message)


# def _retrieve_iottly_info(iottly_path):
#     """
#     Returns iottly project ID and device UUID from settings
#     """
#     iottly_settings_path = os.path.join(
#         iottly_path, "etc", "iottly", "settings.json"
#     )
#     with open(iottly_settings_path) as f:
#         iottly_settings = json.load(f)
#     project_id = iottly_settings["IOTTLY_PROJECT_ID"]
#     device_id = iottly_settings["IOTTLY_MQTT_DEVICE_USER"]
#     return project_id, device_id
#
#
# iottly_path = "/opt/iottly.com-agent"
# project_id, device_id = _retrieve_iottly_info(iottly_path)

app = FastAPI()

origins = [
    "http://localhost",
    "http://localhost:8080",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    return {"name": "", "uuid": "ciao"}

manager = ConnectionManager()

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    print("Before accept")
    await manager.connect(websocket)
    while True:
        data = await websocket.receive_text()
        print(data)
        await manager.broadcast(data)
        # await websocket.send_text(data)
