import os, asyncio, random
from fastapi import FastAPI, WebSocket
from fastapi.responses import HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
from src.agents import triage_agent, dispatch_agent, resolution_agent

app = FastAPI()
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_credentials=True, allow_methods=["*"], allow_headers=["*"])

state = {
    "resources": [
        {"id": "AMB-01", "type": "Ambulance", "lat": 40.758, "lon": -73.985, "status": "Available", "target": None},
        {"id": "FIRE-01", "type": "Fire Truck", "lat": 40.748, "lon": -73.995, "status": "Available", "target": None},
        {"id": "POL-01", "type": "Police", "lat": 40.753, "lon": -73.983, "status": "Available", "target": None},
        {"id": "AMB-02", "type": "Ambulance", "lat": 40.730, "lon": -73.990, "status": "Available", "target": None}
    ],
    "incidents": []
}

CALLS = [("Fire at 42nd St!", 40.752, -73.977), ("Collision on Broadway!", 40.759, -73.984), ("Injury near Park Ave!", 40.761, -73.971)]

@app.get("/")
async def get():
    with open("index.html", "r") as f: return HTMLResponse(f.read())

@app.websocket("/ws")
@app.websocket("/ws/{path:path}")
async def ws_endpoint(websocket: WebSocket, path: str = ""):
    await websocket.accept()
    await websocket.send_json({"type": "init", "resources": state["resources"], "incidents": state["incidents"]})
    while True:
        await asyncio.sleep(8)
        text, lat, lon = random.choice(CALLS)
        inc_data = await triage_agent(text, lat, lon)
        if inc_data:
            inc_data["id"] = f"INC-{random.randint(100,999)}"
            inc_data["status"] = "Pending"
            inc_data["text"] = text
            state["incidents"].insert(0, inc_data)
            await websocket.send_json({"type": "log", "agent": "TRIAGE", "msg": f"Incident {inc_data['id']} localized."})
            unit = dispatch_agent(inc_data, state["resources"])
            if unit:
                await websocket.send_json({"type": "log", "agent": "DISPATCH", "msg": f"Routing {unit['id']} (ETA: {inc_data['eta']}m)"})
                asyncio.create_task(resolution_agent(inc_data['id'], unit['id'], state, websocket))
            await websocket.send_json({"type": "update", "resources": state["resources"], "incidents": state["incidents"]})
