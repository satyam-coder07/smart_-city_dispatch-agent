import streamlit as st
import pandas as pd
import pydeck as pdk
import random, asyncio, time
from datetime import datetime
from src.agents import triage_agent
from src.geo import get_eta

st.set_page_config(page_title="Smart City Dispatch", layout="wide", initial_sidebar_state="collapsed")

# Professional Dark Theme CSS
st.markdown("""
    <style>
    .stApp { background-color: #020617; color: #f8fafc; }
    [data-testid="stMetricValue"] { color: #60a5fa; }
    .agent-log { font-family: monospace; font-size: 0.8rem; padding: 2px 0; }
    .triage { color: #a855f7; } .dispatch { color: #3b82f6; } .res { color: #22c55e; }
    </style>
""", unsafe_allow_html=True)

# Initialize Global State
if "resources" not in st.session_state:
    st.session_state.resources = [
        {"id": "AMB-01", "type": "Ambulance", "lat": 40.758, "lon": -73.985, "status": "Available", "target": None},
        {"id": "FIRE-01", "type": "Fire Truck", "lat": 40.748, "lon": -73.995, "status": "Available", "target": None},
        {"id": "POL-01", "type": "Police", "lat": 40.753, "lon": -73.983, "status": "Available", "target": None}
    ]
if "incidents" not in st.session_state: st.session_state.incidents = []
if "logs" not in st.session_state: st.session_state.logs = []

# --- UI LAYOUT ---
st.title("🏙️ Smart City Dynamic Dispatch Grid")
col1, col2, col3 = st.columns([1, 2, 1])

with col1:
    st.subheader("Active Incidents")
    inc_placeholder = st.empty()

with col2:
    map_placeholder = st.empty()

with col3:
    st.subheader("Fleet & Terminal")
    fleet_placeholder = st.empty()
    st.divider()
    log_placeholder = st.empty()

# --- DISPATCH LOGIC ---
async def run_simulation():
    CALL_DB = [("Fire at 42nd St!", 40.752, -73.977), ("Collision on Broadway!", 40.759, -73.984), ("Injury near Park Ave!", 40.761, -73.971)]
    
    while True:
        # 1. Triage Agent Action
        text, lat, lon = random.choice(CALL_DB)
        new_inc = await triage_agent(text, lat, lon)
        
        if new_inc:
            st.session_state.incidents.insert(0, new_inc)
            st.session_state.logs.append(f"<span class='triage'>[TRIAGE]</span> {new_inc['id']} localized.")
            
            # 2. Dispatch Agent Action
            req = new_inc["resource"]
            avail = [r for r in st.session_state.resources if r["type"] == req and r["status"] == "Available"]
            
            if avail:
                unit = min(avail, key=lambda r: get_eta(new_inc["lat"], new_inc["lon"], r["lat"], r["lon"]))
                unit["status"], unit["target"] = "Dispatched", new_inc["id"]
                new_inc["status"] = "Dispatched"
                st.session_state.logs.append(f"<span class='dispatch'>[DISPATCH]</span> {unit['id']} locked to {new_inc['id']}.")
            else:
                st.session_state.logs.append(f"<span class='dispatch' style='color:red'>[ALERT]</span> No {req} units available!")

        # Refresh UI
        with inc_placeholder.container():
            for i in st.session_state.incidents[:5]:
                st.info(f"**{i['id']}** | {i['resource']}\n{i['text']}")
        
        with fleet_placeholder.container():
            for r in st.session_state.resources:
                color = "🟢" if r["status"] == "Available" else "🔵"
                st.write(f"{color} **{r['id']}** ({r['status']})")

        with log_placeholder.container():
            st.markdown("<div style='height:200px; overflow-y:auto;'>" + "<br>".join(st.session_state.logs[-10:]) + "</div>", unsafe_allow_html=True)
            
        # Map Update
        map_df = pd.DataFrame(st.session_state.resources + st.session_state.incidents)
        map_placeholder.pydeck_chart(pdk.Deck(
            map_style='mapbox://styles/mapbox/dark-v11',
            initial_view_state=pdk.ViewState(latitude=40.75, longitude=-73.98, zoom=12, pitch=45),
            layers=[pdk.Layer('ScatterplotLayer', data=map_df, get_position='[lon, lat]', get_color='[200, 30, 0, 160]', get_radius=200)]
        ))

        await asyncio.sleep(5)
        # 3. Resolution Agent (Cleanup)
        if len(st.session_state.incidents) > 3:
            resolved = st.session_state.incidents.pop()
            for r in st.session_state.resources:
                if r["target"] == resolved["id"]:
                    r["status"], r["target"] = "Available", None
            st.session_state.logs.append(f"<span class='res'>[RES]</span> Incident {resolved['id']} cleared.")

# Launch
if st.button("Start Dispatch Stream"):
    asyncio.run(run_simulation())
