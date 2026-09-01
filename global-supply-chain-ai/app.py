import os
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
from data_generator import generate_global_logistics_data, haversine
from optimizer import DelayPredictor, optimize_supply_chain

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_PATH = os.path.join(BASE_DIR, "global_logistics_data.csv")

st.set_page_config(
    page_title="Global Supply Chain Resilience Engine",
    layout="wide",
    page_icon="🌍",
)

st.title("🌍 Global Multi-Modal Supply Chain Resilience & ESG Engine")
st.markdown(
    "**Enterprise AI Platform** | Real-Time Route Optimization, Dynamic"
    " Infrastructure & Chokepoint Controls"
)
st.divider()

# --- 1. KÜRESEL ŞEHİR VE ALTYAPI VERİTABANI ---
GLOBAL_HUBS_DB = {
    "Istanbul, TR": {
        "lat": 41.0082,
        "lon": 28.9784,
        "continent": "EU",
        "has_port": True,
        "has_airport": True,
        "has_rail": True,
    },
    "Rotterdam, NL": {
        "lat": 51.9244,
        "lon": 4.4777,
        "continent": "EU",
        "has_port": True,
        "has_airport": True,
        "has_rail": True,
    },
    "Hamburg, DE": {
        "lat": 53.5511,
        "lon": 9.9937,
        "continent": "EU",
        "has_port": True,
        "has_airport": True,
        "has_rail": True,
    },
    "Zurich, CH": {
        "lat": 47.3769,
        "lon": 8.5417,
        "continent": "EU",
        "has_port": False,
        "has_airport": True,
        "has_rail": True,
    },
    "Vienna, AT": {
        "lat": 48.2082,
        "lon": 16.3738,
        "continent": "EU",
        "has_port": False,
        "has_airport": True,
        "has_rail": True,
    },
    "Shanghai, CN": {
        "lat": 31.2304,
        "lon": 121.4737,
        "continent": "AS",
        "has_port": True,
        "has_airport": True,
        "has_rail": True,
    },
    "Almaty, KZ": {
        "lat": 43.2220,
        "lon": 76.8512,
        "continent": "AS",
        "has_port": False,
        "has_airport": True,
        "has_rail": True,
    },
    "Dubai, AE": {
        "lat": 25.2048,
        "lon": 55.2708,
        "continent": "ME",
        "has_port": True,
        "has_airport": True,
        "has_rail": False,
    },
    "New York, US": {
        "lat": 40.7128,
        "lon": -74.0060,
        "continent": "NA",
        "has_port": True,
        "has_airport": True,
        "has_rail": True,
    },
}

# --- 2. GERÇEKÇİ LOJİSTİK PARAMETRELERİ ---
# circuity: Kuş uçuşu mesafeyi gerçek yol mesafesine çeviren katsayı
# fixed_op_days: Gümrük, liman elleçleme, yükleme/boşaltma bekleme süresi
MODE_CONFIGS = {
    "Air Freight": {
        "cost_per_km": 2.10,
        "speed_kmh": 700,
        "circuity": 1.10,
        "fixed_op_days": 0.5,
        "co2": 0.0006,
    },
    "Road Freight": {
        "cost_per_km": 0.95,
        "speed_kmh": 50,
        "circuity": 1.30,
        "fixed_op_days": 1.5,
        "co2": 0.00035,
    },
    "Rail Freight": {
        "cost_per_km": 0.55,
        "speed_kmh": 30,
        "circuity": 1.35,
        "fixed_op_days": 3.0,
        "co2": 0.00018,
    },
    "Sea Freight": {
        "cost_per_km": 0.25,
        "speed_kmh": 25,
        "circuity": 1.40,
        "fixed_op_days": 3.5,
        "co2": 0.00008,
    },
}

CHOKEPOINTS_DB = {
    "Strait of Gibraltar (ES/MA)": {
        "affected_regions": [("EU", "NA"), ("AS", "NA")],
        "detour_km": 5200,
        "detour_days": 9.5,
        "cost_penalty": 3100,
    },
    "Suez Canal (Egypt)": {
        "affected_regions": [("EU", "AS"), ("AS", "EU")],
        "detour_km": 6500,
        "detour_days": 11.5,
        "cost_penalty": 3500,
    },
    "Panama Canal (Panama)": {
        "affected_regions": [("NA", "AS"), ("AS", "NA")],
        "detour_km": 8000,
        "detour_days": 14.0,
        "cost_penalty": 4500,
    },
    "Kiel Canal (DE)": {
        "affected_regions": [("EU", "EU")],
        "detour_km": 800,
        "detour_days": 1.5,
        "cost_penalty": 700,
    },
    "Dover Strait / English Channel (UK/FR)": {
        "affected_regions": [("EU", "NA"), ("EU", "EU")],
        "detour_km": 1200,
        "detour_days": 2.0,
        "cost_penalty": 950,
    },
}


# --- 3. DİNAMİK MANTIK FONKSİYONLARI ---
def get_infrastructure_supported_modes(origin, destination):
    orig = GLOBAL_HUBS_DB.get(
        origin,
        {
            "continent": "EU",
            "has_port": True,
            "has_airport": True,
            "has_rail": True,
        },
    )
    dest = GLOBAL_HUBS_DB.get(
        destination,
        {
            "continent": "NA",
            "has_port": True,
            "has_airport": True,
            "has_rail": True,
        },
    )

    feasible_modes = []
    if orig["has_airport"] and dest["has_airport"]:
        feasible_modes.append("Air Freight")
    if orig["has_port"] and dest["has_port"]:
        feasible_modes.append("Sea Freight")
    if orig["continent"] == dest["continent"]:
        if orig["has_rail"] and dest["has_rail"]:
            feasible_modes.append("Rail Freight")
        feasible_modes.append("Road Freight")

    return feasible_modes


def calculate_chokepoint_impact(
    origin, destination, mode, blocked_chokepoints
):
    if "Sea" not in mode or not blocked_chokepoints:
        return 0, 0, 0, False

    orig_cont = GLOBAL_HUBS_DB.get(origin, {}).get("continent", "EU")
    dest_cont = GLOBAL_HUBS_DB.get(destination, {}).get("continent", "NA")

    total_extra_km, total_extra_days, total_extra_cost, is_affected = (
        0,
        0,
        0,
        False,
    )

    for cp_name in blocked_chokepoints:
        cp_info = CHOKEPOINTS_DB.get(cp_name, {})
        affected_pairs = cp_info.get("affected_regions", [])
        if (orig_cont, dest_cont) in affected_pairs or (
            dest_cont,
            orig_cont,
        ) in affected_pairs:
            total_extra_km += cp_info["detour_km"]
            total_extra_days += cp_info["detour_days"]
            total_extra_cost += cp_info["cost_penalty"]
            is_affected = True

    return total_extra_km, total_extra_days, total_extra_cost, is_affected


# --- 4. ARAYÜZ VE SIDEBAR ---
st.sidebar.header("📍 Route Selection")
all_hub_names = sorted(list(GLOBAL_HUBS_DB.keys()))

selected_origin = st.sidebar.selectbox(
    "1. Çıkış Noktası (Origin):", options=all_hub_names, index=0
)
dest_options = [h for h in all_hub_names if h != selected_origin]
selected_dest = st.sidebar.selectbox(
    "2. Varış Noktası (Destination):",
    options=dest_options,
    index=min(1, len(dest_options) - 1),
)

st.sidebar.divider()
st.sidebar.header("🎯 C-Level Strategy Priorities")
cost_weight = st.sidebar.slider("💰 Cost Priority (%)", 0.0, 1.0, 0.4, 0.05)
time_weight = st.sidebar.slider(
    "⏱️ Transit & Delay Priority (%)", 0.0, 1.0, 0.3, 0.05
)
co2_weight = st.sidebar.slider(
    "🌱 CO2 Emission Priority (%)", 0.0, 1.0, 0.3, 0.05
)

st.sidebar.divider()
st.sidebar.header("⛔ Global Chokepoint Blocker")
blocked_canals = st.sidebar.multiselect(
    "Kapalı / Riskli Boğaz ve Kanalları Seçin:",
    options=list(CHOKEPOINTS_DB.keys()),
    default=[],
)

# --- 5. ROTA HESAPLAMA MOTORU ---
feasible_modes = get_infrastructure_supported_modes(
    selected_origin, selected_dest
)
orig_info = GLOBAL_HUBS_DB[selected_origin]
dest_info = GLOBAL_HUBS_DB[selected_dest]
haversine_dist_km = haversine(
    orig_info["lat"], orig_info["lon"], dest_info["lat"], dest_info["lon"]
)

candidate_rows = []
for m in feasible_modes:
    cfg = MODE_CONFIGS[m]
    extra_km, extra_days, extra_cost, is_choked = calculate_chokepoint_impact(
        selected_origin, selected_dest, m, blocked_canals
    )

    # Gerçekçi Yol Mesafesi & Süre Hesaplaması
    actual_distance = (haversine_dist_km * cfg["circuity"]) + extra_km
    pure_travel_hours = actual_distance / cfg["speed_kmh"]
    transit_days = round(
        (pure_travel_hours / 24) + cfg["fixed_op_days"] + extra_days, 1
    )
    final_cost = round((actual_distance * cfg["cost_per_km"]) + extra_cost, 2)

    candidate_rows.append({
        "Shipment_ID": (
            f"ROUTE-{selected_origin[:3]}-{selected_dest[:3]}-{m[:2]}".upper()
        ),
        "Origin_Name": selected_origin,
        "Origin_Lat": orig_info["lat"],
        "Origin_Lon": orig_info["lon"],
        "Destination_Name": selected_dest,
        "Destination_Lat": dest_info["lat"],
        "Destination_Lon": dest_info["lon"],
        "Transport_Mode": m + (" (Detoured)" if is_choked else ""),
        "Distance_KM": round(actual_distance, 1),
        "Base_Cost_USD": final_cost,
        "Transit_Days": transit_days,
        "CO2_Emissions_Tons": round(actual_distance * cfg["co2"], 2),
        "Geopolitical_Risk": "High" if is_choked else "Low",
        "Weather_Condition": "Clear",
        "Port_Congestion_Index": 7.5 if is_choked else 3.5,
        "Delay_Days": 1.2 if is_choked else 0.8,
    })

route_candidates = pd.DataFrame(candidate_rows)

# Optimizasyon Algoritmasını Çalıştır
optimal_route = optimize_supply_chain(
    route_candidates, cost_weight, time_weight, co2_weight
)

# --- PANEL 1: SEÇİLEN KORİDOR VE ALTYAPI DURUMU ---
st.subheader("📍 Active Corridor Infrastructure Status")
st.markdown(f"### 🚀 **{selected_origin}** ➡️ **{selected_dest}**")

bcol1, bcol2 = st.columns(2)
bcol1.caption(
    f"**{selected_origin} Infrastructure:** Port:"
    f" {'✅' if orig_info['has_port'] else '❌ (No Sea)'} | Airport:"
    f" {'✅' if orig_info['has_airport'] else '❌ (No Air)'} | Rail:"
    f" {'✅' if orig_info['has_rail'] else '❌ (No Rail)'}"
)
bcol2.caption(
    f"**{selected_dest} Infrastructure:** Port:"
    f" {'✅' if dest_info['has_port'] else '❌ (No Sea)'} | Airport:"
    f" {'✅' if dest_info['has_airport'] else '❌ (No Air)'} | Rail:"
    f" {'✅' if dest_info['has_rail'] else '❌ (No Rail)'}"
)

total_eta = round(
    optimal_route["Transit_Days"] + optimal_route["Delay_Days"], 1
)

m1, m2, m3, m4, m5 = st.columns(5)
m1.metric("Selected Route ID", optimal_route["Shipment_ID"])
m2.metric("Optimal Mode", optimal_route["Transport_Mode"])
m3.metric("Base Transit Time", f"{optimal_route['Transit_Days']} Days")
m4.metric("AI Predicted Delay", f"+{optimal_route['Delay_Days']} Days")
m5.metric(
    "Total Estimated ETA",
    f"{total_eta} Days",
    delta=f"{optimal_route['Delay_Days']} Days Delay",
    delta_color="inverse",
)

st.divider()

# --- PANEL 2: BENCHMARK TABLOSU ---
st.subheader("⚖️ Modal Feasibility & Cost Benchmark")
st.caption(
    "Gerçekçi mesafe katsayıları ve operasyonel süreler dahil güncel sonuçlar:"
)
st.table(
    route_candidates[[
        "Transport_Mode",
        "Distance_KM",
        "Base_Cost_USD",
        "Transit_Days",
        "CO2_Emissions_Tons",
        "Geopolitical_Risk",
    ]]
)
