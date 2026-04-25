import os, json, random
from groq import Groq

async def triage_agent(call_text, lat, lon, api_key):
    if not api_key:
        # Fallback to mock data if key is missing
        return {"id": f"INC-{random.randint(100,999)}", "severity": "High", "resource": "Ambulance", "lat": lat, "lon": lon, "status": "Pending", "text": call_text}
    
    try:
        client = Groq(api_key=api_key)
        prompt = f"Parse 911 call: '{call_text}'. Return JSON keys: 'severity' (High/Med), 'resource' (Ambulance/Fire Truck/Police)."
        resp = client.chat.completions.create(
            messages=[{"role": "user", "content": prompt}], 
            model="llama3-8b-8192", 
            response_format={"type": "json_object"}
        )
        data = json.loads(resp.choices[0].message.content)
        return {
            "id": f"INC-{random.randint(100,999)}", 
            "severity": data.get("severity", "High"), 
            "resource": data.get("resource", "Ambulance"), 
            "lat": lat, "lon": lon, 
            "status": "Pending", 
            "text": call_text
        }
    except Exception as e:
        return {"id": f"ERR-01", "severity": "High", "resource": "Ambulance", "lat": lat, "lon": lon, "status": "Error", "text": f"LLM Error: {str(e)}"}
