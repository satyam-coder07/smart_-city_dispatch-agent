import streamlit as st
import pandas as pd
import pydeck as pdk
import random, asyncio
from src.agents import triage_agent
from src.geo import get_eta

st.set_page_config(page_title="Smart City Dispatch", layout="wide", initial_sidebar_state="expanded")

# Professional UI Styling
st.markdown("""
    <style>
    .stApp { background-color: #020617; color: #f8fafc; }
    .triage { color: #a855f7; font-weight: bold; }
    .dispatch { color: #3b82f6; font-weight: bold; }
    .res { color: #22c55e; font-weight: bold; }
    .log-container { 
        background-color: #000; 
        padding: 10px; 
        border-radius: 5px; 
        height: 250px; 
        overflow-y: auto; 
        font-family: monospace;
        border: 1px solid #1e293b;
    }
    </style>
""", unsafe_allow_html=True)

# Sidebar for Configuration
with st.sidebar:
    st.header("🔑 Config")
    user_api_key = st.text_input("Groq API Key", type="password", placeholder="gsk_...")
    st.info("Enter your key to enable real-time Llama-3 Triage.")

# Initialize State
if "resources" not in st.session_state:
    st.session_state.resources = [
        {"id": "AMB-01", "type": "Ambulance", "lat": 40.758, "lon": -73.985, "status": "Available", "target": None},
        {"id": "FIRE-01", "type": "Fire Truck", "lat": 40.748, "lon": -73.995, "status": "Available", "target": None},
        {"id": "POL-01", "type": "Police", "lat": 40.753, "lon": -73.983, "status": "Available", "target": None},
        {"id": "AMB-02", "type": "Ambulance", "lat": 40.730, "lon": -73.990, "status": "Available", "target": None}
    ]
if "incidents" not in st.session_state: st.session_state.incidents = []
if "logs" not in st.session_state: st.session_state.logs = []

st.title("🏙️ Smart City Dynamic Dispatch Grid")
st.caption("3-Node Autonomous Agent Swarm: Triage | Dispatch | Resolution")

col1, col2, col3 = st.columns([1, 2, 1])

with col1:
    st.subheader("Active Grid")
    inc_placeholder = st.empty()

with col2:
    st.subheader("Tactical Map")
    map_placeholder = st.empty()

with col3:
    st.subheader("Fleet Status")
    fleet_placeholder = st.empty()
    st.subheader("Swarm Terminal")
    log_placeholder = st.empty()

async def run_swarm():
    CALL_DB = [
        {"text": "Fire at 42nd St station!", "lat": 40.752, "lon": -73.977},
        {"text": "Major collision on Broadway!", "lat": 40.759, "lon": -73.984},
        {"text": "Medical emergency near Central Park!", "lat": 40.761, "lon": -73.971}
    ]
    
    while True:
        call = random.choice(CALL_DB)
        # Pass the key from the sidebar to the agent
        new_inc = await triage_agent(call["text"], call["lat"], call["lon"], user_api_key)
        
        if new_inc:
            st.session_state.incidents.insert(0, new_inc)
            st.session_state.logs.append(f"<span class='triage'>[TRIAGE]</span> Parsed {new_inc['id']}")
            
            req = new_inc["resource"]
            avail = [r for r in st.session_state.resources if r["type"] == req and r["status"] == "Available"]
            
            if avail:
                unit = min(avail, key=lambda r: get_eta(new_inc["lat"], new_inc["lon"], r["lat"], r["lon"]))
                unit["status"], unit["target"] = "Dispatched", new_inc["id"]
                new_inc["status"] = "Dispatched"
                st.session_state.logs.append(f"<span class='dispatch'>[DISPATCH]</span> Unit {unit['id']} routed.")
            else:
                st.session_state.logs.append("<span style='color:red'>[SYSTEM]</span> Critical Resource Shortage!")

        # Update Displays
        inc_placeholder.write(pd.DataFrame(st.session_state.incidents).drop(columns=['lat', 'lon']) if st.session_state.incidents else "Awaiting Data...")
        fleet_placeholder.write(pd.DataFrame(st.session_state.resources))
        log_placeholder.markdown(f"<div class='log-container'>{'<br>'.join(st.session_state.logs[-12:])}</div>", unsafe_allow_html=True)
        
        # Tactical Map Rendering
        all_points = pd.DataFrame(st.session_state.resources + st.session_state.incidents)
        map_placeholder.pydeck_chart(pdk.Deck(
            map_style='mapbox://styles/mapbox/dark-v11',
            initial_view_state=pdk.ViewState(latitude=40.75, longitude=-73.98, zoom=12, pitch=45),
            layers=[pdk.Layer('ScatterplotLayer', data=all_points, get_position='[lon, lat]', get_color='[60, 160, 255, 200]', get_radius=180)]
        ))

        await asyncio.sleep(6)
        
        if len(st.session_state.incidents) > 2:
            resolved = st.session_state.incidents.pop()
            for r in st.session_state.resources:
                if r["target"] == resolved["id"]:
                    r["status"], r["target"] = "Available", None
            st.session_state.logs.append(f"<span class='res'>[RESOLVE]</span> Incident {resolved['id']} cleared.")

if st.button("Initialize Swarm Stream", use_container_width=True):
    if not user_api_key:
        st.warning("Running in MOCK MODE (No API Key provided).")
    asyncio.run(run_swarm())
