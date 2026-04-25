import os, json, random, asyncio
from groq import Groq
from src.geo import get_eta

client = Groq(api_key=os.environ.get("GROQ_API_KEY", ""))

async def triage_agent(call_text, lat, lon):
    if not os.environ.get("GROQ_API_KEY"):
        return {"severity": "High", "resource": "Ambulance", "lat": lat, "lon": lon}
    prompt = f"Parse 911 call: '{call_text}'. Return JSON keys: 'severity' (High/Med), 'resource' (Ambulance/Fire Truck/Police)."
    try:
        resp = client.chat.completions.create(messages=[{"role": "user", "content": prompt}], model="llama3-8b-8192", response_format={"type": "json_object"})
        data = json.loads(resp.choices[0].message.content)
        return {**data, "lat": lat, "lon": lon}
    except: return None

def dispatch_agent(incident, resources):
    req = incident.get("resource", "Ambulance")
    avail = [r for r in resources if r["type"] == req and r["status"] == "Available"]
    if not avail: return None
    best = min(avail, key=lambda r: get_eta(incident["lat"], incident["lon"], r["lat"], r["lon"]))
    best.update({"status": "Dispatched", "target": incident["id"]})
    incident.update({"status": "Dispatched", "eta": get_eta(incident["lat"], incident["lon"], best["lat"], best["lon"])})
    return best

async def resolution_agent(inc_id, res_id, state, websocket):
    await asyncio.sleep(12)
    for r in state["resources"]:
        if r["id"] == res_id: r.update({"status": "Available", "target": None})
    state["incidents"][:] = [i for i in state["incidents"] if i["id"] != inc_id]
    await websocket.send_json({"type": "log", "agent": "RESOLUTION", "msg": f"Unit {res_id} cleared scene {inc_id}."})
    await websocket.send_json({"type": "update", "resources": state["resources"], "incidents": state["incidents"]})
