import os
import requests
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
    "**Enterprise AI Platform** | Dynamic Global Route Optimization, Port Intelligence & A/B Scenario Engine"
)
st.divider()

# --- 1. KÜRESEL ŞEHİR VE ALTYAPI VERİTABANI ---
GLOBAL_HUBS_DB = {
    # --- AVRUPA & TÜRKİYE ---
    "Istanbul, TR": {"lat": 41.0082, "lon": 28.9784, "continent": "EU", "has_port": True, "has_airport": True, "has_rail": True, "base_congestion": 4.5},
    "Rotterdam, NL": {"lat": 51.9244, "lon": 4.4777, "continent": "EU", "has_port": True, "has_airport": True, "has_rail": True, "base_congestion": 6.0},
    "Hamburg, DE": {"lat": 53.5511, "lon": 9.9937, "continent": "EU", "has_port": True, "has_airport": True, "has_rail": True, "base_congestion": 5.5},
    "London, GB": {"lat": 51.5074, "lon": -0.1278, "continent": "EU", "has_port": True, "has_airport": True, "has_rail": True, "base_congestion": 4.0},
    "Antwerp, BE": {"lat": 51.2194, "lon": 4.4025, "continent": "EU", "has_port": True, "has_airport": True, "has_rail": True, "base_congestion": 5.8},
    "Zurich, CH": {"lat": 47.3769, "lon": 8.5417, "continent": "EU", "has_port": False, "has_airport": True, "has_rail": True, "base_congestion": 2.0},
    "Vienna, AT": {"lat": 48.2082, "lon": 16.3738, "continent": "EU", "has_port": False, "has_airport": True, "has_rail": True, "base_congestion": 2.0},
    "Warsaw, PL": {"lat": 52.2297, "lon": 21.0122, "continent": "EU", "has_port": False, "has_airport": True, "has_rail": True, "base_congestion": 2.5},
    "Piraeus, GR": {"lat": 37.9475, "lon": 23.6431, "continent": "EU", "has_port": True, "has_airport": True, "has_rail": True, "base_congestion": 5.0},
    "Moscow, RU": {"lat": 55.7558, "lon": 37.6173, "continent": "EU", "has_port": False, "has_airport": True, "has_rail": True, "base_congestion": 3.0},

    # --- ASYA ---
    "Shanghai, CN": {"lat": 31.2304, "lon": 121.4737, "continent": "AS", "has_port": True, "has_airport": True, "has_rail": True, "base_congestion": 8.5},
    "Shenzhen, CN": {"lat": 22.5431, "lon": 114.0579, "continent": "AS", "has_port": True, "has_airport": True, "has_rail": True, "base_congestion": 8.0},
    "Xi'an, CN": {"lat": 34.3416, "lon": 108.9398, "continent": "AS", "has_port": False, "has_airport": True, "has_rail": True, "base_congestion": 3.0},
    "Singapore, SG": {"lat": 1.3521, "lon": 103.8198, "continent": "AS", "has_port": True, "has_airport": True, "has_rail": False, "base_congestion": 7.5},
    "Tokyo, JP": {"lat": 35.6762, "lon": 139.6503, "continent": "AS", "has_port": True, "has_airport": True, "has_rail": True, "base_congestion": 4.5},
    "Busan, KR": {"lat": 35.1796, "lon": 129.0756, "continent": "AS", "has_port": True, "has_airport": True, "has_rail": True, "base_congestion": 6.2},
    "Mumbai, IN": {"lat": 19.0760, "lon": 72.8777, "continent": "AS", "has_port": True, "has_airport": True, "has_rail": True, "base_congestion": 6.8},
    "Colombo, LK": {"lat": 6.9271, "lon": 79.8612, "continent": "AS", "has_port": True, "has_airport": True, "has_rail": True, "base_congestion": 5.5},

    # --- ORTA DOĞU ---
    "Dubai, AE": {"lat": 25.2048, "lon": 55.2708, "continent": "ME", "has_port": True, "has_airport": True, "has_rail": False, "base_congestion": 5.2},
    "Jeddah, SA": {"lat": 21.5433, "lon": 39.1728, "continent": "ME", "has_port": True, "has_airport": True, "has_rail": True, "base_congestion": 5.8},

    # --- KUZEY AMERİKA ---
    "New York, US": {"lat": 40.7128, "lon": -74.0060, "continent": "NA", "has_port": True, "has_airport": True, "has_rail": True, "base_congestion": 6.5},
    "Los Angeles, US": {"lat": 34.0522, "lon": -118.2437, "continent": "NA", "has_port": True, "has_airport": True, "has_rail": True, "base_congestion": 7.8},

    # --- GÜNEY AMERİKA & AFRİKA ---
    "Santos, BR": {"lat": -23.9618, "lon": -46.3322, "continent": "SA", "has_port": True, "has_airport": True, "has_rail": True, "base_congestion": 6.0},
    "Alexandria, EG": {"lat": 31.2001, "lon": 29.9187, "continent": "AF", "has_port": True, "has_airport": True, "has_rail": True, "base_congestion": 5.5},
}

MODE_CONFIGS = {
    "Air Freight": {"cost_per_km": 2.10, "effective_speed_kmh": 350, "circuity": 1.10, "fixed_op_days": 1.5, "co2": 0.0006},
    "Road Freight": {"cost_per_km": 0.95, "effective_speed_kmh": 25, "circuity": 1.30, "fixed_op_days": 1.0, "co2": 0.00035},
    "Rail Freight": {"cost_per_km": 0.55, "effective_speed_kmh": 20, "circuity": 1.35, "fixed_op_days": 2.0, "co2": 0.00018},
    "Sea Freight": {"cost_per_km": 0.25, "effective_speed_kmh": 22, "circuity": 1.40, "fixed_op_days": 4.5, "co2": 0.00008},
}

CHOKEPOINTS_DB = {
    "Strait of Gibraltar (ES/MA)": {"affected_regions": [("EU", "NA"), ("AS", "NA"), ("ME", "NA")], "detour_km": 11500, "detour_days": 18.0, "cost_penalty": 4200},
    "Suez Canal (Egypt)": {"affected_regions": [("EU", "AS"), ("AS", "EU"), ("EU", "ME")], "detour_km": 6500, "detour_days": 11.5, "cost_penalty": 3500},
    "Panama Canal (Panama)": {"affected_regions": [("NA", "AS"), ("AS", "NA"), ("EU", "NA")], "detour_km": 8000, "detour_days": 14.0, "cost_penalty": 4500},
    "Strait of Malacca (SG/ID/MY)": {"affected_regions": [("AS", "EU"), ("AS", "ME")], "detour_km": 3000, "detour_days": 5.0, "cost_penalty": 1800},
    "Bab el-Mandeb (Red Sea)": {"affected_regions": [("EU", "AS"), ("AS", "EU"), ("EU", "ME")], "detour_km": 6000, "detour_days": 10.0, "cost_penalty": 2900},
    "Bosporus / Dardanelles (TR)": {"affected_regions": [("EU", "AS")], "detour_km": 1500, "detour_days": 3.0, "cost_penalty": 1200},
}

MED_BLACK_SEA_HUBS = {"Istanbul, TR", "Piraeus, GR", "Alexandria, EG"}
NORTH_ATLANTIC_EU_HUBS = {"Rotterdam, NL", "Hamburg, DE", "Antwerp, BE", "London, GB"}


@st.cache_data(ttl=1800)
def fetch_live_weather(lat, lon):
    try:
        url = f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&current_weather=true"
        resp = requests.get(url, timeout=3).json()
        curr = resp.get("current_weather", {})
        temp = curr.get("temperature", 20.0)
        wind = curr.get("windspeed", 10.0)
        weather_desc = "Clear"
        weather_delay = 0.0
        if wind > 35.0:
            weather_desc = "Stormy & High Wind"
            weather_delay = 1.5
        elif wind > 20.0:
            weather_desc = "Windy / Rain"
            weather_delay = 0.5
        return {"temp": temp, "wind_speed": wind, "condition": weather_desc, "delay_impact": weather_delay}
    except Exception:
        return {"temp": 20.0, "wind_speed": 12.0, "condition": "Clear (Simulated)", "delay_impact": 0.0}


def estimate_port_congestion_ais(port_name, weather_wind, is_choked):
    port_data = GLOBAL_HUBS_DB.get(port_name, {"base_congestion": 5.0})
    base_idx = port_data.get("base_congestion", 5.0)
    wind_penalty = 1.5 if weather_wind > 35.0 else (0.8 if weather_wind > 20.0 else 0.0)
    choke_penalty = 2.0 if is_choked else 0.0
    estimated_idx = min(10.0, round(base_idx + wind_penalty + choke_penalty, 1))
    estimated_delay_days = round((estimated_idx / 10.0) * 3.5, 1)
    return estimated_idx, estimated_delay_days


def get_maritime_waypoints(origin, destination, is_detoured=False):
    is_origin_med = origin in MED_BLACK_SEA_HUBS
    is_dest_north = destination in NORTH_ATLANTIC_EU_HUBS
    is_origin_north = origin in NORTH_ATLANTIC_EU_HUBS
    is_dest_med = destination in MED_BLACK_SEA_HUBS

    pts = []
    if (is_origin_med and is_dest_north) or (is_origin_north and is_dest_med):
        if not is_detoured:
            if origin == "Istanbul, TR" or destination == "Istanbul, TR":
                pts.append((39.8, 25.8))
            if origin in ["Istanbul, TR", "Piraeus, GR"] or destination in ["Istanbul, TR", "Piraeus, GR"]:
                pts.append((36.2, 22.5))
            pts.extend([(37.2, 11.2), (36.1, -5.3), (43.5, -9.6), (48.2, -5.2), (50.8, 1.4)])
        else:
            if origin == "Istanbul, TR" or destination == "Istanbul, TR":
                pts.append((39.8, 25.8))
            pts.extend([(33.0, 32.5), (12.5, 43.5), (-34.8, 20.0), (0.0, -10.0), (48.2, -5.2), (50.8, 1.4)])

        if is_origin_north and is_dest_med:
            pts = pts[::-1]

    return pts


def get_infrastructure_supported_modes(origin, destination):
    orig = GLOBAL_HUBS_DB.get(origin, {"continent": "EU", "has_port": True, "has_airport": True, "has_rail": True})
    dest = GLOBAL_HUBS_DB.get(destination, {"continent": "NA", "has_port": True, "has_airport": True, "has_rail": True})

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


def calculate_chokepoint_impact(origin, destination, mode, blocked_chokepoints):
    if "Sea" not in mode or not blocked_chokepoints:
        return 0, 0, 0, False

    orig_cont = GLOBAL_HUBS_DB.get(origin, {}).get("continent", "EU")
    dest_cont = GLOBAL_HUBS_DB.get(destination, {}).get("continent", "NA")

    total_extra_km, total_extra_days, total_extra_cost, is_affected = 0, 0, 0, False

    for cp_name in blocked_chokepoints:
        cp_info = CHOKEPOINTS_DB.get(cp_name, {})
        affected_pairs = cp_info.get("affected_regions", [])
        if (orig_cont, dest_cont) in affected_pairs or (dest_cont, orig_cont) in affected_pairs:
            total_extra_km += cp_info["detour_km"]
            total_extra_days += cp_info["detour_days"]
            total_extra_cost += cp_info["cost_penalty"]
            is_affected = True

    return total_extra_km, total_extra_days, total_extra_cost, is_affected


def generate_multimodal_routes(origin, destination, cargo_val, wacc, carbon_tax_rate, blocked_chokepoints=[], port_delay_override=0.0):
    orig_info = GLOBAL_HUBS_DB[origin]
    dest_info = GLOBAL_HUBS_DB[destination]
    direct_dist = haversine(orig_info["lat"], orig_info["lon"], dest_info["lat"], dest_info["lon"])

    best_hub = None
    best_extra_ratio = float("inf")
    best_d1, best_d2 = 0, 0

    for hub_name, hub_info in GLOBAL_HUBS_DB.items():
        if hub_name in [origin, destination]:
            continue
        d1 = haversine(orig_info["lat"], orig_info["lon"], hub_info["lat"], hub_info["lon"])
        d2 = haversine(hub_info["lat"], hub_info["lon"], dest_info["lat"], dest_info["lon"])
        total_via_hub = d1 + d2
        ratio = total_via_hub / direct_dist if direct_dist > 0 else 1.0

        if ratio < 1.35 and ratio < best_extra_ratio:
            best_extra_ratio = ratio
            best_hub = hub_name
            best_d1 = d1
            best_d2 = d2

    if not best_hub:
        return pd.DataFrame()

    hub_info = GLOBAL_HUBS_DB[best_hub]

    seg1_speed = 25.0 if orig_info["continent"] == hub_info["continent"] and orig_info["has_rail"] else 22.0
    seg1_op = 1.0 if seg1_speed == 25.0 else 2.0
    seg2_speed = 25.0 if hub_info["continent"] == dest_info["continent"] else 22.0
    seg2_op = 1.0 if seg2_speed == 25.0 else 2.0

    seg1_days = ((best_d1 * 1.3) / (seg1_speed * 24)) + seg1_op
    seg2_days = ((best_d2 * 1.3) / (seg2_speed * 24)) + seg2_op
    hub_transshipment_dwell = 2.5 + port_delay_override

    extra_km, extra_days, extra_cost, is_choked = calculate_chokepoint_impact(
        best_hub, destination, "Sea Freight", blocked_chokepoints
    )

    total_dist = (best_d1 * 1.3) + (best_d2 * 1.3) + extra_km
    total_transit_days = round(seg1_days + hub_transshipment_dwell + seg2_days + extra_days, 1)
    base_cost = round((best_d1 * 0.45) + (best_d2 * 0.75) + 500.0 + extra_cost, 2)

    holding_cost = round(cargo_val * (wacc / 100.0) * (total_transit_days / 365.0), 2)
    co2_tons = round((best_d1 * 0.00012) + (best_d2 * 0.00025), 2)
    carbon_tax_cost = round(co2_tons * carbon_tax_rate, 2)

    total_landed_cost = round(base_cost + holding_cost + carbon_tax_cost, 2)

    return pd.DataFrame([{
        "Shipment_ID": f"MULTI-{origin[:3]}-{best_hub[:3]}-{destination[:3]}".upper(),
        "Origin_Name": origin,
        "Origin_Lat": orig_info["lat"],
        "Origin_Lon": orig_info["lon"],
        "Destination_Name": destination,
        "Destination_Lat": dest_info["lat"],
        "Destination_Lon": dest_info["lon"],
        "Hub_Name": best_hub,
        "Hub_Lat": hub_info["lat"],
        "Hub_Lon": hub_info["lon"],
        "Transport_Mode": f"Multimodal (Trans-Hub: {best_hub.split(',')[0]})" + (" (Detoured)" if is_choked else ""),
        "Distance_KM": round(total_dist, 1),
        "Base_Cost_USD": base_cost,
        "Inventory_Holding_Cost_USD": holding_cost,
        "Carbon_Tax_USD": carbon_tax_cost,
        "Total_Landed_Cost_USD": total_landed_cost,
        "Transit_Days": total_transit_days,
        "CO2_Emissions_Tons": co2_tons,
        "Geopolitical_Risk": "High" if is_choked else "Low",
        "Weather_Condition": "Clear",
        "Port_Congestion_Index": 6.5 if is_choked else 4.0,
        "Delay_Days": round(1.5 + port_delay_override if is_choked else 0.8 + port_delay_override, 1),
    }])


# --- HESAPLAMA MOTORU (SIMULATION ENGINE FUNCTION) ---
def run_scenario_engine(origin, destination, cargo_val, wacc, carbon_tax, blocked_canals, manual_port_delay, cost_w, time_w, co2_w):
    orig_info = GLOBAL_HUBS_DB[origin]
    dest_info = GLOBAL_HUBS_DB[destination]
    orig_weather = fetch_live_weather(orig_info["lat"], orig_info["lon"])
    dest_weather = fetch_live_weather(dest_info["lat"], dest_info["lon"])

    auto_dest_idx, auto_dest_delay = estimate_port_congestion_ais(destination, dest_weather["wind_speed"], len(blocked_canals) > 0)
    effective_port_delay = manual_port_delay if manual_port_delay is not None else auto_dest_delay

    total_weather_delay = orig_weather["delay_impact"] + dest_weather["delay_impact"]
    feasible_modes = get_infrastructure_supported_modes(origin, destination)
    haversine_dist_km = haversine(orig_info["lat"], orig_info["lon"], dest_info["lat"], dest_info["lon"])

    candidate_rows = []
    for m in feasible_modes:
        cfg = MODE_CONFIGS[m]
        extra_km, extra_days, extra_cost, is_choked = calculate_chokepoint_impact(origin, destination, m, blocked_canals)

        actual_distance = (haversine_dist_km * cfg["circuity"]) + extra_km
        pure_travel_hours = actual_distance / cfg["effective_speed_kmh"]

        mode_port_delay = effective_port_delay if m == "Sea Freight" else (effective_port_delay * 0.3)

        transit_days = round((pure_travel_hours / 24) + cfg["fixed_op_days"] + extra_days + mode_port_delay, 1)
        base_cost = round((actual_distance * cfg["cost_per_km"]) + extra_cost, 2)

        holding_cost = round(cargo_val * (wacc / 100.0) * (transit_days / 365.0), 2)
        co2_tons = round(actual_distance * cfg["co2"], 2)
        carbon_tax_cost = round(co2_tons * carbon_tax, 2)

        total_landed_cost = round(base_cost + holding_cost + carbon_tax_cost, 2)

        weather_delay_adj = total_weather_delay if m in ["Sea Freight", "Air Freight"] else 0.2

        candidate_rows.append({
            "Shipment_ID": f"ROUTE-{origin[:3]}-{destination[:3]}-{m[:2]}".upper(),
            "Origin_Name": origin,
            "Origin_Lat": orig_info["lat"],
            "Origin_Lon": orig_info["lon"],
            "Destination_Name": destination,
            "Destination_Lat": dest_info["lat"],
            "Destination_Lon": dest_info["lon"],
            "Transport_Mode": m + (" (Detoured)" if is_choked else ""),
            "Distance_KM": round(actual_distance, 1),
            "Base_Cost_USD": base_cost,
            "Inventory_Holding_Cost_USD": holding_cost,
            "Carbon_Tax_USD": carbon_tax_cost,
            "Total_Landed_Cost_USD": total_landed_cost,
            "Transit_Days": transit_days,
            "CO2_Emissions_Tons": co2_tons,
            "Geopolitical_Risk": "High" if is_choked else "Low",
            "Weather_Condition": orig_weather["condition"],
            "Port_Congestion_Index": auto_dest_idx if m == "Sea Freight" else 3.5,
            "Delay_Days": round((1.2 if is_choked else 0.8) + weather_delay_adj, 1),
        })

    route_candidates = pd.DataFrame(candidate_rows)

    mm_df = generate_multimodal_routes(origin, destination, cargo_val, wacc, carbon_tax, blocked_canals, effective_port_delay)
    if not mm_df.empty:
        route_candidates = pd.concat([route_candidates, mm_df], ignore_index=True)

    optimal_route = optimize_supply_chain(route_candidates, cost_w, time_w, co2_w)
    total_eta = round(optimal_route["Transit_Days"] + optimal_route["Delay_Days"], 1)

    return {
        "route_candidates": route_candidates,
        "optimal_route": optimal_route,
        "total_eta": total_eta,
        "orig_weather": orig_weather,
        "dest_weather": dest_weather,
        "effective_port_delay": effective_port_delay,
    }


# --- VERİ YÜKLEME ---
@st.cache_data
def load_data():
    if os.path.exists(DATA_PATH):
        return pd.read_csv(DATA_PATH)
    else:
        df_gen = generate_global_logistics_data()
        df_gen.to_csv(DATA_PATH, index=False)
        return df_gen


df = load_data()


@st.cache_resource
def get_trained_model(dataframe):
    predictor = DelayPredictor()
    predictor.train(dataframe)
    return predictor


predictor = get_trained_model(df)
all_hub_names = sorted(list(GLOBAL_HUBS_DB.keys()))

# --- TABS GEZİNTİSİ ---
tab1, tab2 = st.tabs([
    "🚀 Tekil Rota Optimizasyonu & Canlı Analiz",
    "⚖️ A/B Senaryo Kıyaslama (Side-by-Side Comparison)"
])

# ==========================================
# TAB 1: TEKİL ROTA OPTİMİZASYONU
# ==========================================
with tab1:
    st.sidebar.header("📍 Global Route Selection")
    selected_origin = st.sidebar.selectbox("1. Çıkış Noktası (Origin):", options=all_hub_names, index=0, key="t1_orig")
    dest_options = [h for h in all_hub_names if h != selected_origin]
    selected_dest = st.sidebar.selectbox("2. Varış Noktası (Destination):", options=dest_options, index=min(1, len(dest_options) - 1), key="t1_dest")

    st.sidebar.divider()
    st.sidebar.header("📦 Cargo & Financial Parameters")
    cargo_value = st.sidebar.number_input("Cargo Value ($):", min_value=1000, value=500000, step=25000, key="t1_cargo")
    wacc_rate = st.sidebar.slider("Annual Holding / WACC Rate (%):", 1.0, 30.0, 15.0, 0.5, key="t1_wacc")

    st.sidebar.divider()
    st.sidebar.header("🌱 ESG & EU ETS Carbon Tax")
    carbon_tax_rate = st.sidebar.number_input("Carbon Tax / EU ETS ($/Ton CO2):", min_value=0.0, value=85.0, step=5.0, key="t1_ctax")

    st.sidebar.divider()
    st.sidebar.header("⚓ Port Congestion & AIS Override")
    use_manual_port_delay = st.sidebar.checkbox("Manuel Liman Gecikmesi Gir (Acente/Saha Bilgisi)", value=False, key="t1_manual_check")

    orig_info = GLOBAL_HUBS_DB[selected_origin]
    dest_info = GLOBAL_HUBS_DB[selected_dest]
    orig_weather = fetch_live_weather(orig_info["lat"], orig_info["lon"])
    dest_weather = fetch_live_weather(dest_info["lat"], dest_info["lon"])
    auto_dest_idx, auto_dest_delay = estimate_port_congestion_ais(selected_dest, dest_weather["wind_speed"], False)

    if use_manual_port_delay:
        effective_port_delay = st.sidebar.slider("Varış Limanı Manuel Bekleme Süresi (+Gün):", 0.0, 7.0, float(auto_dest_delay), 0.5, key="t1_delay_slider")
    else:
        effective_port_delay = auto_dest_delay

    st.sidebar.divider()
    st.sidebar.header("🎯 C-Level Strategy Priorities")
    cost_weight = st.sidebar.slider("💰 Cost Priority (%)", 0.0, 1.0, 0.4, 0.05, key="t1_cw")
    time_weight = st.sidebar.slider("⏱️ Transit & Delay Priority (%)", 0.0, 1.0, 0.3, 0.05, key="t1_tw")
    co2_weight = st.sidebar.slider("🌱 CO2 Emission Priority (%)", 0.0, 1.0, 0.3, 0.05, key="t1_co2w")

    st.sidebar.divider()
    st.sidebar.header("⛔ Global Chokepoint Blocker")
    blocked_canals = st.sidebar.multiselect("Kapalı / Riskli Boğaz ve Kanallar:", options=list(CHOKEPOINTS_DB.keys()), default=[], key="t1_choke")

    # ÇALIŞTIR
    res = run_scenario_engine(
        selected_origin, selected_dest, cargo_value, wacc_rate, carbon_tax_rate,
        blocked_canals, effective_port_delay if use_manual_port_delay else None,
        cost_weight, time_weight, co2_weight
    )

    optimal_route = res["optimal_route"]
    route_candidates = res["route_candidates"]
    total_eta = res["total_eta"]

    # PANEL 1: BAŞLIK VE CANLI DURUM
    st.subheader("📍 Active Corridor Infrastructure & Live Conditions")
    st.markdown(f"### 🚀 **{selected_origin}** ➡️ **{selected_dest}**")

    wcol1, wcol2 = st.columns(2)
    wcol1.info(f"🌤️ **{selected_origin} Weather:** {res['orig_weather']['temp']}°C | Wind: {res['orig_weather']['wind_speed']} km/h | **{res['orig_weather']['condition']}**")
    wcol2.info(f"🌤️ **{selected_dest} Weather:** {res['dest_weather']['temp']}°C | Wind: {res['dest_weather']['wind_speed']} km/h | **{res['dest_weather']['condition']}**")

    st.warning(f"⚓ **Port Dwell Impact ({selected_dest}):** Added Delay: **+{res['effective_port_delay']} Days**")

    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Optimal Mode", optimal_route["Transport_Mode"])
    m2.metric("Freight Cost", f"${optimal_route['Base_Cost_USD']:,.2f}")
    m3.metric("Inventory Holding Cost", f"${optimal_route['Inventory_Holding_Cost_USD']:,.2f}")
    m4.metric("EU ETS Carbon Tax", f"${optimal_route['Carbon_Tax_USD']:,.2f}")

    m5, m6 = st.columns(2)
    m5.metric("Total Landed Cost", f"${optimal_route['Total_Landed_Cost_USD']:,.2f}")
    m6.metric("Total ETA (Incl. Delay)", f"{total_eta} Days")

    st.divider()

    # PANEL 2: TABLO VİZÜALİZASYON
    st.subheader("⚖️ Modal Feasibility & Financial Landed Cost Benchmark")
    st.table(route_candidates[[
        "Transport_Mode", "Distance_KM", "Base_Cost_USD", "Inventory_Holding_Cost_USD",
        "Carbon_Tax_USD", "Total_Landed_Cost_USD", "Transit_Days", "CO2_Emissions_Tons", "Geopolitical_Risk"
    ]])

    st.divider()

    # PANEL 3: HARİTA VE MALİYET DAĞILIMI
    col_left, col_right = st.columns([2, 1])

    with col_left:
        st.subheader("🌐 Global Route Map")
        fig = go.Figure()
        fig.add_trace(go.Scattergeo(
            lon=[h["lon"] for h in GLOBAL_HUBS_DB.values()],
            lat=[h["lat"] for h in GLOBAL_HUBS_DB.values()],
            hovertext=list(GLOBAL_HUBS_DB.keys()),
            mode="markers", marker=dict(size=6, color="#1f77b4"), name="Logistics Hubs"
        ))

        opt_mode = str(optimal_route["Transport_Mode"])
        is_sea = "Sea Freight" in opt_mode
        is_det = "Detoured" in opt_mode

        if is_sea:
            sea_pts = get_maritime_waypoints(selected_origin, selected_dest, is_detoured=is_det)
            if sea_pts:
                route_lats = [optimal_route["Origin_Lat"]] + [p[0] for p in sea_pts] + [optimal_route["Destination_Lat"]]
                route_lons = [optimal_route["Origin_Lon"]] + [p[1] for p in sea_pts] + [optimal_route["Destination_Lon"]]
            else:
                route_lats = [optimal_route["Origin_Lat"], optimal_route["Destination_Lat"]]
                route_lons = [optimal_route["Origin_Lon"], optimal_route["Destination_Lon"]]
        else:
            route_lats = [optimal_route["Origin_Lat"], optimal_route["Destination_Lat"]]
            route_lons = [optimal_route["Origin_Lon"], optimal_route["Destination_Lon"]]

        fig.add_trace(go.Scattergeo(
            lon=route_lons, lat=route_lats, mode="lines+markers",
            line=dict(width=3, color="#ef553b"), name=f"OPTIMAL ({optimal_route['Transport_Mode']})"
        ))

        fig.update_layout(geo=dict(projection_type="natural earth", showland=True, landcolor="rgb(240, 240, 240)"), margin=dict(l=0, r=0, t=30, b=0), height=400)
        st.plotly_chart(fig, use_container_width=True)

    with col_right:
        st.subheader("📊 Financial Cost Breakdown")
        cost_df = route_candidates.melt(
            id_vars=["Transport_Mode"],
            value_vars=["Base_Cost_USD", "Inventory_Holding_Cost_USD", "Carbon_Tax_USD"],
            var_name="Cost_Type", value_name="USD"
        )
        fig_bar = px.bar(cost_df, x="Transport_Mode", y="USD", color="Cost_Type", barmode="stack")
        st.plotly_chart(fig_bar, use_container_width=True)


# ==========================================
# TAB 2: A/B SENARYO KIYASLAMA MODU
# ==========================================
with tab2:
    st.subheader("⚖️ Side-by-Side Scenario Comparison & Sensitivity Analysis")
    st.markdown("İki farklı lojistik stratejisini veya kriz senaryosunu yan yana simüle edip **Landed Cost**, **ETA** ve **CO2 Emisyonu** farklarını anlık kıyaslayın.")

    # SENARYO GİRDİ PANELİ (SUTUNLAR)
    scen_col1, scen_col2 = st.columns(2)

    with scen_col1:
        st.info("### 🟢 Senaryo A (Mevcut / Baz Senaryo)")
        sa_orig = st.selectbox("Çıkış (Origin) [A]:", options=all_hub_names, index=all_hub_names.index("Shanghai, CN"), key="sa_orig")
        sa_dest_opts = [h for h in all_hub_names if h != sa_orig]
        sa_dest = st.selectbox("Varış (Destination) [A]:", options=sa_dest_opts, index=sa_dest_opts.index("Rotterdam, NL") if "Rotterdam, NL" in sa_dest_opts else 0, key="sa_dest")

        sa_cargo = st.number_input("Yük Değeri ($) [A]:", min_value=1000, value=600000, step=50000, key="sa_cargo")
        sa_wacc = st.slider("WACC / Holding Rate (%) [A]:", 1.0, 30.0, 15.0, key="sa_wacc")
        sa_ctax = st.number_input("Karbon Vergisi ($/Ton) [A]:", min_value=0.0, value=85.0, step=5.0, key="sa_ctax")
        sa_choke = st.multiselect("Kapalı Boğazlar [A]:", options=list(CHOKEPOINTS_DB.keys()), default=[], key="sa_choke")
        sa_delay = st.slider("Liman Bekleme Ekranı (+Gün) [A]:", 0.0, 10.0, 1.0, key="sa_delay")

    with scen_col2:
        st.error("### 🔴 Senaryo B (Kriz / Alternatif Strateji)")
        sb_orig = st.selectbox("Çıkış (Origin) [B]:", options=all_hub_names, index=all_hub_names.index("Shanghai, CN"), key="sb_orig")
        sb_dest_opts = [h for h in all_hub_names if h != sb_orig]
        sb_dest = st.selectbox("Varış (Destination) [B]:", options=sb_dest_opts, index=sb_dest_opts.index("Rotterdam, NL") if "Rotterdam, NL" in sb_dest_opts else 0, key="sb_dest")

        sb_cargo = st.number_input("Yük Değeri ($) [B]:", min_value=1000, value=600000, step=50000, key="sb_cargo")
        sb_wacc = st.slider("WACC / Holding Rate (%) [B]:", 1.0, 30.0, 15.0, key="sb_wacc")
        sb_ctax = st.number_input("Karbon Vergisi ($/Ton) [B]:", min_value=0.0, value=120.0, step=5.0, key="sb_ctax")
        sb_choke = st.multiselect("Kapalı Boğazlar [B]:", options=list(CHOKEPOINTS_DB.keys()), default=["Suez Canal (Egypt)", "Bab el-Mandeb (Red Sea)"], key="sb_choke")
        sb_delay = st.slider("Liman Bekleme Ekranı (+Gün) [B]:", 0.0, 10.0, 3.5, key="sb_delay")

    st.divider()

    # MOTORLARI ÇALIŞTIR
    res_A = run_scenario_engine(sa_orig, sa_dest, sa_cargo, sa_wacc, sa_ctax, sa_choke, sa_delay, 0.4, 0.3, 0.3)
    res_B = run_scenario_engine(sb_orig, sb_dest, sb_cargo, sb_wacc, sb_ctax, sb_choke, sb_delay, 0.4, 0.3, 0.3)

    opt_A = res_A["optimal_route"]
    opt_B = res_B["optimal_route"]

    delta_cost = opt_B["Total_Landed_Cost_USD"] - opt_A["Total_Landed_Cost_USD"]
    delta_cost_pct = (delta_cost / opt_A["Total_Landed_Cost_USD"]) * 100 if opt_A["Total_Landed_Cost_USD"] > 0 else 0
    delta_eta = res_B["total_eta"] - res_A["total_eta"]
    delta_co2 = opt_B["CO2_Emissions_Tons"] - opt_A["CO2_Emissions_Tons"]

    # METRİK DELTA KARTLARI
    st.subheader("📊 Executive Delta Comparison (Senaryo B - Senaryo A)")

    mc1, mc2, mc3, mc4 = st.columns(4)
    mc1.metric(
        label="Total Landed Cost Difference",
        value=f"${opt_B['Total_Landed_Cost_USD']:,.2f}",
        delta=f"{'+' if delta_cost >= 0 else ''}${delta_cost:,.2f} ({delta_cost_pct:+.1f}%)",
        delta_color="inverse"
    )
    mc2.metric(
        label="Total ETA Difference",
        value=f"{res_B['total_eta']} Days",
        delta=f"{'+' if delta_eta >= 0 else ''}{delta_eta:.1f} Days",
        delta_color="inverse"
    )
    mc3.metric(
        label="CO2 Emissions Difference",
        value=f"{opt_B['CO2_Emissions_Tons']} Tons",
        delta=f"{'+' if delta_co2 >= 0 else ''}{delta_co2:.2f} Tons",
        delta_color="inverse"
    )
    mc4.metric(
        label="Optimal Mode Shift",
        value=f"B: {opt_B['Transport_Mode'].split(' ')[0]}",
        delta=f"A: {opt_A['Transport_Mode'].split(' ')[0]}",
        delta_color="off"
    )

    st.divider()

    # YAN YANA METRİK VE GRAFİK KIYASLAMASI
    col_ab1, col_ab2 = st.columns(2)

    with col_ab1:
        st.markdown("#### 🟢 Senaryo A Sonuçları")
        st.write(f"**Optimal Rota:** {opt_A['Transport_Mode']}")
        st.write(f"• Freight Cost: **${opt_A['Base_Cost_USD']:,.2f}**")
        st.write(f"• Inventory Holding Cost: **${opt_A['Inventory_Holding_Cost_USD']:,.2f}**")
        st.write(f"• Carbon Tax Cost: **${opt_A['Carbon_Tax_USD']:,.2f}**")
        st.write(f"• **Total Landed Cost:** **${opt_A['Total_Landed_Cost_USD']:,.2f}**")
        st.write(f"• **Total ETA:** **{res_A['total_eta']} Days**")

    with col_ab2:
        st.markdown("#### 🔴 Senaryo B Sonuçları")
        st.write(f"**Optimal Rota:** {opt_B['Transport_Mode']}")
        st.write(f"• Freight Cost: **${opt_B['Base_Cost_USD']:,.2f}**")
        st.write(f"• Inventory Holding Cost: **${opt_B['Inventory_Holding_Cost_USD']:,.2f}**")
        st.write(f"• Carbon Tax Cost: **${opt_B['Carbon_Tax_USD']:,.2f}**")
        st.write(f"• **Total Landed Cost:** **${opt_B['Total_Landed_Cost_USD']:,.2f}**")
        st.write(f"• **Total ETA:** **{res_B['total_eta']} Days**")

    # KIYASLAMA BAR GRAFİĞİ
    st.subheader("📈 Financial Breakdown Comparison (Scenario A vs Scenario B)")
    
    comp_data = pd.DataFrame([
        {"Scenario": "Scenario A", "Cost_Type": "Freight Cost", "USD": opt_A["Base_Cost_USD"]},
        {"Scenario": "Scenario A", "Cost_Type": "Holding Cost", "USD": opt_A["Inventory_Holding_Cost_USD"]},
        {"Scenario": "Scenario A", "Cost_Type": "Carbon Tax", "USD": opt_A["Carbon_Tax_USD"]},
        {"Scenario": "Scenario B", "Cost_Type": "Freight Cost", "USD": opt_B["Base_Cost_USD"]},
        {"Scenario": "Scenario B", "Cost_Type": "Holding Cost", "USD": opt_B["Inventory_Holding_Cost_USD"]},
        {"Scenario": "Scenario B", "Cost_Type": "Carbon Tax", "USD": opt_B["Carbon_Tax_USD"]},
    ])

    fig_comp = px.bar(
        comp_data, x="Scenario", y="USD", color="Cost_Type",
        title="Side-by-Side Cost Stack Comparison", barmode="stack", text_auto=".2s"
    )
    st.plotly_chart(fig_comp, use_container_width=True)

    # C-LEVEL KIYASLAMA ÖZETİ
    st.subheader("📝 Executive Scenario Recommendation")

    if delta_cost > 0:
        st.error(
            f"⚠️ **Kriz/Disruption Uyarısı:** Senaryo B, Senaryo A'ya kıyasla toplam maliyeti **${delta_cost:,.2f} (+%{delta_cost_pct:.1f})** artırmaktadır. "
            f"Ek olarak transit süre **+{delta_eta:.1f} gün** uzamaktadır. Tedarik zinciri kırılmasını önlemek için alternatif multimodal hub'ların (örneğin demiryolu veya hava-deniz kombinasyonu) değerlendirilmesi önerilir."
        )
    else:
        st.success(
            f"✅ **Optimizasyon Fırsatı:** Senaryo B, Senaryo A'ya kıyasla **${abs(delta_cost):,.2f}** tasarruf sağlamaktadır. "
            f"Transit süredeki değişim **{delta_eta:+.1f} gün** olarak hesaplanmıştır."
        )
