import os, json, random, asyncio
from groq import Groq
from src.geo import get_eta

def get_client():
    api_key = os.environ.get("GROQ_API_KEY") or st.secrets.get("GROQ_API_KEY")
    return Groq(api_key=api_key) if api_key else None

async def triage_agent(call_text, lat, lon):
    client = get_client()
    if not client:
        return {"id": f"INC-{random.randint(100,999)}", "severity": "High", "resource": "Ambulance", "lat": lat, "lon": lon, "status": "Pending", "text": call_text}
    
    prompt = f"Parse 911 call: '{call_text}'. Return JSON keys: 'severity' (High/Med), 'resource' (Ambulance/Fire Truck/Police)."
    try:
        resp = client.chat.completions.create(messages=[{"role": "user", "content": prompt}], model="llama3-8b-8192", response_format={"type": "json_object"})
        data = json.loads(resp.choices[0].message.content)
        return {"id": f"INC-{random.randint(100,999)}", "severity": data.get("severity", "High"), "resource": data.get("resource", "Ambulance"), "lat": lat, "lon": lon, "status": "Pending", "text": call_text}
    except: return None
