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
    "**Enterprise AI Platform** | Dynamic Global Route Optimization & Real-World Logistics Intelligence"
)
st.divider()

# --- 1. KÜRESEL ŞEHİR VE ALTYAPI VERİTABANI ---
GLOBAL_HUBS_DB = {
    # --- AVRUPA & TÜRKİYE ---
    "Istanbul, TR": {"lat": 41.0082, "lon": 28.9784, "continent": "EU", "has_port": True, "has_airport": True, "has_rail": True},
    "Rotterdam, NL": {"lat": 51.9244, "lon": 4.4777, "continent": "EU", "has_port": True, "has_airport": True, "has_rail": True},
    "Hamburg, DE": {"lat": 53.5511, "lon": 9.9937, "continent": "EU", "has_port": True, "has_airport": True, "has_rail": True},
    "London, GB": {"lat": 51.5074, "lon": -0.1278, "continent": "EU", "has_port": True, "has_airport": True, "has_rail": True},
    "Antwerp, BE": {"lat": 51.2194, "lon": 4.4025, "continent": "EU", "has_port": True, "has_airport": True, "has_rail": True},
    "Zurich, CH": {"lat": 47.3769, "lon": 8.5417, "continent": "EU", "has_port": False, "has_airport": True, "has_rail": True},
    "Vienna, AT": {"lat": 48.2082, "lon": 16.3738, "continent": "EU", "has_port": False, "has_airport": True, "has_rail": True},
    "Warsaw, PL": {"lat": 52.2297, "lon": 21.0122, "continent": "EU", "has_port": False, "has_airport": True, "has_rail": True},
    "Piraeus, GR": {"lat": 37.9475, "lon": 23.6431, "continent": "EU", "has_port": True, "has_airport": True, "has_rail": True},
    "Moscow, RU": {"lat": 55.7558, "lon": 37.6173, "continent": "EU", "has_port": False, "has_airport": True, "has_rail": True},

    # --- ASYA ---
    "Shanghai, CN": {"lat": 31.2304, "lon": 121.4737, "continent": "AS", "has_port": True, "has_airport": True, "has_rail": True},
    "Shenzhen, CN": {"lat": 22.5431, "lon": 114.0579, "continent": "AS", "has_port": True, "has_airport": True, "has_rail": True},
    "Xi'an, CN": {"lat": 34.3416, "lon": 108.9398, "continent": "AS", "has_port": False, "has_airport": True, "has_rail": True},
    "Singapore, SG": {"lat": 1.3521, "lon": 103.8198, "continent": "AS", "has_port": True, "has_airport": True, "has_rail": False},
    "Tokyo, JP": {"lat": 35.6762, "lon": 139.6503, "continent": "AS", "has_port": True, "has_airport": True, "has_rail": True},
    "Busan, KR": {"lat": 35.1796, "lon": 129.0756, "continent": "AS", "has_port": True, "has_airport": True, "has_rail": True},
    "Mumbai, IN": {"lat": 19.0760, "lon": 72.8777, "continent": "AS", "has_port": True, "has_airport": True, "has_rail": True},
    "Colombo, LK": {"lat": 6.9271, "lon": 79.8612, "continent": "AS", "has_port": True, "has_airport": True, "has_rail": True},
    "Almaty, KZ": {"lat": 43.2220, "lon": 76.8512, "continent": "AS", "has_port": False, "has_airport": True, "has_rail": True},
    "Baku, AZ": {"lat": 40.4093, "lon": 49.8671, "continent": "AS", "has_port": True, "has_airport": True, "has_rail": True},
    "Tashkent, UZ": {"lat": 41.2995, "lon": 69.2401, "continent": "AS", "has_port": False, "has_airport": True, "has_rail": True},
    "Vladivostok, RU": {"lat": 43.1155, "lon": 131.8855, "continent": "AS", "has_port": True, "has_airport": True, "has_rail": True},

    # --- ORTA DOĞU ---
    "Dubai, AE": {"lat": 25.2048, "lon": 55.2708, "continent": "ME", "has_port": True, "has_airport": True, "has_rail": False},
    "Riyadh, SA": {"lat": 24.7136, "lon": 46.6753, "continent": "ME", "has_port": False, "has_airport": True, "has_rail": True},
    "Jeddah, SA": {"lat": 21.5433, "lon": 39.1728, "continent": "ME", "has_port": True, "has_airport": True, "has_rail": True},
    "Salalah, OM": {"lat": 17.0151, "lon": 54.0924, "continent": "ME", "has_port": True, "has_airport": True, "has_rail": False},

    # --- KUZEY AMERİKA ---
    "New York, US": {"lat": 40.7128, "lon": -74.0060, "continent": "NA", "has_port": True, "has_airport": True, "has_rail": True},
    "Los Angeles, US": {"lat": 34.0522, "lon": -118.2437, "continent": "NA", "has_port": True, "has_airport": True, "has_rail": True},
    "Chicago, US": {"lat": 41.8781, "lon": -87.6298, "continent": "NA", "has_port": False, "has_airport": True, "has_rail": True},
    "Vancouver, CA": {"lat": 49.2827, "lon": -123.1207, "continent": "NA", "has_port": True, "has_airport": True, "has_rail": True},
    "Toronto, CA": {"lat": 43.6532, "lon": -79.3832, "continent": "NA", "has_port": False, "has_airport": True, "has_rail": True},
    "Mexico City, MX": {"lat": 19.4326, "lon": -99.1332, "continent": "NA", "has_port": False, "has_airport": True, "has_rail": True},

    # --- GÜNEY AMERİKA ---
    "Santos, BR": {"lat": -23.9618, "lon": -46.3322, "continent": "SA", "has_port": True, "has_airport": True, "has_rail": True},
    "Buenos Aires, AR": {"lat": -34.6037, "lon": -58.3816, "continent": "SA", "has_port": True, "has_airport": True, "has_rail": True},
    "Santiago, CL": {"lat": -33.4489, "lon": -70.6693, "continent": "SA", "has_port": False, "has_airport": True, "has_rail": True},
    "Bogota, CO": {"lat": 4.7110, "lon": -74.0721, "continent": "SA", "has_port": False, "has_airport": True, "has_rail": False},

    # --- AFRİKA ---
    "Cairo, EG": {"lat": 30.0444, "lon": 31.2357, "continent": "AF", "has_port": False, "has_airport": True, "has_rail": True},
    "Alexandria, EG": {"lat": 31.2001, "lon": 29.9187, "continent": "AF", "has_port": True, "has_airport": True, "has_rail": True},
    "Durban, ZA": {"lat": -29.8587, "lon": 31.0218, "continent": "AF", "has_port": True, "has_airport": True, "has_rail": True},
    "Cape Town, ZA": {"lat": -33.9249, "lon": 18.4241, "continent": "AF", "has_port": True, "has_airport": True, "has_rail": True},
    "Lagos, NG": {"lat": 6.5244, "lon": 3.3792, "continent": "AF", "has_port": True, "has_airport": True, "has_rail": False},
    "Mombasa, KE": {"lat": -4.0435, "lon": 39.6682, "continent": "AF", "has_port": True, "has_airport": True, "has_rail": True},
    "Casablanca, MA": {"lat": 33.5731, "lon": -7.5898, "continent": "AF", "has_port": True, "has_airport": True, "has_rail": True},

    # --- OKYANUSYA ---
    "Sydney, AU": {"lat": -33.8688, "lon": 151.2093, "continent": "OC", "has_port": True, "has_airport": True, "has_rail": True},
    "Melbourne, AU": {"lat": -37.8136, "lon": 144.9631, "continent": "OC", "has_port": True, "has_airport": True, "has_rail": True},
    "Auckland, NZ": {"lat": -36.8485, "lon": 174.7633, "continent": "OC", "has_port": True, "has_airport": True, "has_rail": False},
}

MODE_CONFIGS = {
    "Air Freight": {"cost_per_km": 2.10, "effective_speed_kmh": 350, "circuity": 1.10, "fixed_op_days": 1.5, "co2": 0.0006},
    "Road Freight": {"cost_per_km": 0.95, "effective_speed_kmh": 25, "circuity": 1.30, "fixed_op_days": 1.0, "co2": 0.00035},
    "Rail Freight": {"cost_per_km": 0.55, "effective_speed_kmh": 20, "circuity": 1.35, "fixed_op_days": 2.0, "co2": 0.00018},
    "Sea Freight": {"cost_per_km": 0.25, "effective_speed_kmh": 22, "circuity": 1.40, "fixed_op_days": 4.5, "co2": 0.00008},
}

CHOKEPOINTS_DB = {
    "Strait of Gibraltar (ES/MA)": {
        "affected_regions": [("EU", "NA"), ("AS", "NA"), ("ME", "NA"), ("EU", "SA"), ("EU", "AF")],
        "detour_km": 11500,
        "detour_days": 18.0,
        "cost_penalty": 4200,
    },
    "Suez Canal (Egypt)": {
        "affected_regions": [("EU", "AS"), ("AS", "EU"), ("EU", "ME"), ("EU", "OC")],
        "detour_km": 6500,
        "detour_days": 11.5,
        "cost_penalty": 3500,
    },
    "Panama Canal (Panama)": {
        "affected_regions": [("NA", "AS"), ("AS", "NA"), ("EU", "NA"), ("NA", "SA")],
        "detour_km": 8000,
        "detour_days": 14.0,
        "cost_penalty": 4500,
    },
    "Strait of Malacca (SG/ID/MY)": {
        "affected_regions": [("AS", "EU"), ("AS", "ME"), ("AS", "AF")],
        "detour_km": 3000,
        "detour_days": 5.0,
        "cost_penalty": 1800,
    },
    "Bab el-Mandeb (Red Sea)": {
        "affected_regions": [("EU", "AS"), ("AS", "EU"), ("EU", "ME")],
        "detour_km": 6000,
        "detour_days": 10.0,
        "cost_penalty": 2900,
    },
    "Strait of Hormuz (Persian Gulf)": {
        "affected_regions": [("ME", "AS"), ("ME", "EU"), ("EU", "ME")],
        "detour_km": 2500,
        "detour_days": 4.5,
        "cost_penalty": 2100,
    },
    "Bosporus / Dardanelles (TR)": {
        "affected_regions": [("EU", "AS")],
        "detour_km": 1500,
        "detour_days": 3.0,
        "cost_penalty": 1200,
    },
    "Cape of Good Hope (ZA)": {
        "affected_regions": [("EU", "AS"), ("AS", "EU")],
        "detour_km": 4500,
        "detour_days": 8.0,
        "cost_penalty": 2500,
    },
}

MED_BLACK_SEA_HUBS = {"Istanbul, TR", "Piraeus, GR", "Alexandria, EG"}
NORTH_ATLANTIC_EU_HUBS = {"Rotterdam, NL", "Hamburg, DE", "Antwerp, BE", "London, GB"}


def get_maritime_waypoints(origin, destination, is_detoured=False):
    """Deniz yolu çizilirken kalkış limanına göre akıllı deniz koridoru ara noktaları üretir."""
    is_origin_med = origin in MED_BLACK_SEA_HUBS
    is_dest_north = destination in NORTH_ATLANTIC_EU_HUBS
    is_origin_north = origin in NORTH_ATLANTIC_EU_HUBS
    is_dest_med = destination in MED_BLACK_SEA_HUBS

    pts = []
    if (is_origin_med and is_dest_north) or (is_origin_north and is_dest_med):
        if not is_detoured:
            # Çanakkale Boğazı sadece İstanbul çıkışlı/varışlı ise eklenir
            if origin == "Istanbul, TR" or destination == "Istanbul, TR":
                pts.append((39.8, 25.8))
            
            # İstanbul veya Yunanistan için Mora Burnu dönülür
            if origin in ["Istanbul, TR", "Piraeus, GR"] or destination in ["Istanbul, TR", "Piraeus, GR"]:
                pts.append((36.2, 22.5))
            
            # Akdeniz - Atlantik Ortak Deniz Rotası
            pts.extend([
                (37.2, 11.2),   # Sicilya Kanalı
                (36.1, -5.3),   # Cebelitarık Boğazı
                (43.5, -9.6),   # İspanya / Atlantik Açıkları
                (48.2, -5.2),   # Manş Denizi Girişi
                (50.8, 1.4),    # Dover Boğazı
            ])
        else:
            # Cebelitarık Kapalı / Cape Detour Rotası
            if origin == "Istanbul, TR" or destination == "Istanbul, TR":
                pts.append((39.8, 25.8))
            
            pts.extend([
                (33.0, 32.5),   # Doğu Akdeniz
                (12.5, 43.5),   # Babülmendep Boğazı
                (-34.8, 20.0),  # Ümit Burnu
                (0.0, -10.0),   # Atlantik Ekvator Hattı
                (48.2, -5.2),   # Manş Denizi Girişi
                (50.8, 1.4),    # Dover Boğazı
            ])

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

        if cp_name == "Strait of Gibraltar (ES/MA)":
            is_med_to_north_sea = (
                (origin in MED_BLACK_SEA_HUBS and destination in NORTH_ATLANTIC_EU_HUBS) or
                (destination in MED_BLACK_SEA_HUBS and origin in NORTH_ATLANTIC_EU_HUBS)
            )
            is_cross_continent = (
                (orig_cont, dest_cont) in cp_info.get("affected_regions", []) or
                (dest_cont, orig_cont) in cp_info.get("affected_regions", [])
            )

            if is_med_to_north_sea or is_cross_continent:
                total_extra_km += cp_info["detour_km"]
                total_extra_days += cp_info["detour_days"]
                total_extra_cost += cp_info["cost_penalty"]
                is_affected = True
        else:
            affected_pairs = cp_info.get("affected_regions", [])
            if (orig_cont, dest_cont) in affected_pairs or (dest_cont, orig_cont) in affected_pairs:
                total_extra_km += cp_info["detour_km"]
                total_extra_days += cp_info["detour_days"]
                total_extra_cost += cp_info["cost_penalty"]
                is_affected = True

    return total_extra_km, total_extra_days, total_extra_cost, is_affected


def generate_multimodal_routes(origin, destination, blocked_chokepoints=[]):
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
    hub_transshipment_dwell = 2.5

    extra_km, extra_days, extra_cost, is_choked = calculate_chokepoint_impact(
        best_hub, destination, "Sea Freight", blocked_chokepoints
    )

    total_dist = (best_d1 * 1.3) + (best_d2 * 1.3) + extra_km
    total_transit_days = seg1_days + hub_transshipment_dwell + seg2_days + extra_days
    cost = (best_d1 * 0.45) + (best_d2 * 0.75) + 500.0 + extra_cost

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
        "Base_Cost_USD": round(cost, 2),
        "Transit_Days": round(total_transit_days, 1),
        "CO2_Emissions_Tons": round((best_d1 * 0.00012) + (best_d2 * 0.00025), 2),
        "Geopolitical_Risk": "High" if is_choked else "Low",
        "Weather_Condition": "Clear",
        "Port_Congestion_Index": 6.5 if is_choked else 4.0,
        "Delay_Days": 1.5 if is_choked else 0.8,
    }])


# --- 4. VERİ SİSTEMİ VE YÜKLEME ---
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

# --- 5. SIDEBAR & KRİZ SİMÜLATÖRÜ ---
st.sidebar.header("📍 Global Route Selection")

selected_origin = st.sidebar.selectbox("1. Çıkış Noktası (Origin):", options=all_hub_names, index=0)
dest_options = [h for h in all_hub_names if h != selected_origin]
selected_dest = st.sidebar.selectbox("2. Varış Noktası (Destination):", options=dest_options, index=min(1, len(dest_options) - 1))

st.sidebar.divider()
st.sidebar.header("🎯 C-Level Strategy Priorities")
cost_weight = st.sidebar.slider("💰 Cost Priority (%)", 0.0, 1.0, 0.4, 0.05)
time_weight = st.sidebar.slider("⏱️ Transit & Delay Priority (%)", 0.0, 1.0, 0.3, 0.05)
co2_weight = st.sidebar.slider("🌱 CO2 Emission Priority (%)", 0.0, 1.0, 0.3, 0.05)

st.sidebar.divider()
st.sidebar.header("⛔ Global Chokepoint Blocker")
blocked_canals = st.sidebar.multiselect(
    "Kapalı / Riskli Boğaz ve Kanalları Seçin:",
    options=list(CHOKEPOINTS_DB.keys()),
    default=[],
)

# --- 6. HESAPLAMA MOTORU ---
feasible_modes = get_infrastructure_supported_modes(selected_origin, selected_dest)
orig_info = GLOBAL_HUBS_DB[selected_origin]
dest_info = GLOBAL_HUBS_DB[selected_dest]
haversine_dist_km = haversine(orig_info["lat"], orig_info["lon"], dest_info["lat"], dest_info["lon"])

candidate_rows = []
for m in feasible_modes:
    cfg = MODE_CONFIGS[m]
    extra_km, extra_days, extra_cost, is_choked = calculate_chokepoint_impact(selected_origin, selected_dest, m, blocked_canals)

    actual_distance = (haversine_dist_km * cfg["circuity"]) + extra_km
    pure_travel_hours = actual_distance / cfg["effective_speed_kmh"]
    transit_days = round((pure_travel_hours / 24) + cfg["fixed_op_days"] + extra_days, 1)
    final_cost = round((actual_distance * cfg["cost_per_km"]) + extra_cost, 2)

    candidate_rows.append({
        "Shipment_ID": f"ROUTE-{selected_origin[:3]}-{selected_dest[:3]}-{m[:2]}".upper(),
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

mm_df = generate_multimodal_routes(selected_origin, selected_dest, blocked_canals)
if not mm_df.empty:
    route_candidates = pd.concat([route_candidates, mm_df], ignore_index=True)

optimal_route = optimize_supply_chain(route_candidates, cost_weight, time_weight, co2_weight)

# --- PANEL 1: SEÇİLEN KORİDOR VE ALTYAPI DURUMU ---
st.subheader("📍 Active Corridor Infrastructure Status")
st.markdown(f"### 🚀 **{selected_origin}** ➡️ **{selected_dest}**")

bcol1, bcol2 = st.columns(2)
bcol1.caption(
    f"**{selected_origin} Infrastructure:** Port: {'✅' if orig_info['has_port'] else '❌ (No Sea)'} | Airport: {'✅' if orig_info['has_airport'] else '❌ (No Air)'} | Rail: {'✅' if orig_info['has_rail'] else '❌ (No Rail)'}"
)
bcol2.caption(
    f"**{selected_dest} Infrastructure:** Port: {'✅' if dest_info['has_port'] else '❌ (No Sea)'} | Airport: {'✅' if dest_info['has_airport'] else '❌ (No Air)'} | Rail: {'✅' if dest_info['has_rail'] else '❌ (No Rail)'}"
)

total_eta = round(optimal_route["Transit_Days"] + optimal_route["Delay_Days"], 1)

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

st.divider()

# --- PANEL 3: HARİTA GÖRSELLEŞTİRME & GRAFİKLER ---
col_left, col_right = st.columns([2, 1])

with col_left:
    st.subheader("🌐 Global Route Map")
    fig = go.Figure()

    # 1. Tüm Hub'ları Haritaya Ekle
    fig.add_trace(
        go.Scattergeo(
            lon=[h["lon"] for h in GLOBAL_HUBS_DB.values()],
            lat=[h["lat"] for h in GLOBAL_HUBS_DB.values()],
            hovertext=list(GLOBAL_HUBS_DB.keys()),
            mode="markers",
            marker=dict(size=6, color="#1f77b4", opacity=0.7),
            name="Logistics Hubs",
        )
    )

    # 2. Optimal Rota Koordinatlarını Hesapla
    opt_mode = str(optimal_route["Transport_Mode"])
    is_sea_freight = "Sea Freight" in opt_mode
    is_detoured = "Detoured" in opt_mode

    if is_sea_freight:
        sea_pts = get_maritime_waypoints(selected_origin, selected_dest, is_detoured=is_detoured)
        if sea_pts:
            route_lats = [optimal_route["Origin_Lat"]] + [p[0] for p in sea_pts] + [optimal_route["Destination_Lat"]]
            route_lons = [optimal_route["Origin_Lon"]] + [p[1] for p in sea_pts] + [optimal_route["Destination_Lon"]]
        else:
            route_lats = [optimal_route["Origin_Lat"], optimal_route["Destination_Lat"]]
            route_lons = [optimal_route["Origin_Lon"], optimal_route["Destination_Lon"]]
    elif "Hub_Lat" in optimal_route and pd.notnull(optimal_route.get("Hub_Lat")):
        route_lats = [optimal_route["Origin_Lat"], optimal_route["Hub_Lat"], optimal_route["Destination_Lat"]]
        route_lons = [optimal_route["Origin_Lon"], optimal_route["Hub_Lon"], optimal_route["Destination_Lon"]]
    else:
        route_lats = [optimal_route["Origin_Lat"], optimal_route["Destination_Lat"]]
        route_lons = [optimal_route["Origin_Lon"], optimal_route["Destination_Lon"]]

    # 3. Rota Çizgisini Ekle
    fig.add_trace(
        go.Scattergeo(
            lon=route_lons,
            lat=route_lats,
            mode="lines+markers",
            line=dict(width=3, color="#ef553b"),
            marker=dict(size=6, color="#ef553b"),
            name=f"OPTIMAL ({optimal_route['Transport_Mode']})",
        )
    )

    # 4. Dinamik Zoom / Odaklanma Alanı Hesaplama
    lat_margin = max((max(route_lats) - min(route_lats)) * 0.25, 4.0)
    lon_margin = max((max(route_lons) - min(route_lons)) * 0.25, 4.0)

    min_lat, max_lat = min(route_lats) - lat_margin, max(route_lats) + lat_margin
    min_lon, max_lon = min(route_lons) - lon_margin, max(route_lons) + lon_margin

    fig.update_layout(
        geo=dict(
            projection_type="natural earth",
            showland=True,
            landcolor="rgb(240, 240, 240)",
            countrycolor="rgb(200, 200, 200)",
            lataxis_range=[min_lat, max_lat],
            lonaxis_range=[min_lon, max_lon],
        ),
        margin=dict(l=0, r=0, t=30, b=0),
        height=450,
    )
    st.plotly_chart(fig, use_container_width=True)

with col_right:
    st.subheader("📊 Cost Comparison ($)")
    fig_bar = px.bar(
        route_candidates,
        x="Transport_Mode",
        y="Base_Cost_USD",
        color="Transport_Mode",
        title="Freight Cost by Available Mode",
    )
    st.plotly_chart(fig_bar, use_container_width=True)

st.divider()

# --- PANEL 4: C-LEVEL ÖZET ---
st.subheader("📝 Executive Summary")
if blocked_canals:
    st.warning(f"⚠️ **Chokepoint Active Blockage:** **{', '.join(blocked_canals)}** selected as CLOSED.")

st.success(
    f"**Recommended Route:** **{selected_origin}** ➔ **{selected_dest}** via **{optimal_route['Transport_Mode']}** | Total Freight Cost: **${optimal_route['Base_Cost_USD']:,.2f}** | Total ETA: **{total_eta} days**."
)
