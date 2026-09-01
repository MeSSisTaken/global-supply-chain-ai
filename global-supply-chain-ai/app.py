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

# --- 1. KÜRESEL DETAYLI ŞEHİR VE ALTYAPI VERİTABANI ---
GLOBAL_HUBS_DB = {
    # Avrupa & Türkiye
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
    "Warsaw, PL": {
        "lat": 52.2297,
        "lon": 21.0122,
        "continent": "EU",
        "has_port": False,
        "has_airport": True,
        "has_rail": True,
    },
    # Asya & Rusya
    "Shanghai, CN": {
        "lat": 31.2304,
        "lon": 121.4737,
        "continent": "AS",
        "has_port": True,
        "has_airport": True,
        "has_rail": True,
    },
    "Xi'an, CN": {
        "lat": 34.3416,
        "lon": 108.9398,
        "continent": "AS",
        "has_port": False,
        "has_airport": True,
        "has_rail": True,
    },
    "Singapore, SG": {
        "lat": 1.3521,
        "lon": 103.8198,
        "continent": "AS",
        "has_port": True,
        "has_airport": True,
        "has_rail": False,
    },
    "Almaty, KZ": {
        "lat": 43.2220,
        "lon": 76.8512,
        "continent": "AS",
        "has_port": False,
        "has_airport": True,
        "has_rail": True,
    },
    "Baku, AZ": {
        "lat": 40.4093,
        "lon": 49.8671,
        "continent": "AS",
        "has_port": True,
        "has_airport": True,
        "has_rail": True,
    },
    "Vladivostok, RU": {
        "lat": 43.1155,
        "lon": 131.8855,
        "continent": "AS",
        "has_port": True,
        "has_airport": True,
        "has_rail": True,
    },
    "Moscow, RU": {
        "lat": 55.7558,
        "lon": 37.6173,
        "continent": "EU",
        "has_port": False,
        "has_airport": True,
        "has_rail": True,
    },
    # Orta Doğu
    "Dubai, AE": {
        "lat": 25.2048,
        "lon": 55.2708,
        "continent": "ME",
        "has_port": True,
        "has_airport": True,
        "has_rail": False,
    },
    "Riyadh, SA": {
        "lat": 24.7136,
        "lon": 46.6753,
        "continent": "ME",
        "has_port": False,
        "has_airport": True,
        "has_rail": True,
    },
    # Kuzey Amerika
    "New York, US": {
        "lat": 40.7128,
        "lon": -74.0060,
        "continent": "NA",
        "has_port": True,
        "has_airport": True,
        "has_rail": True,
    },
    "Los Angeles, US": {
        "lat": 34.0522,
        "lon": -118.2437,
        "continent": "NA",
        "has_port": True,
        "has_airport": True,
        "has_rail": True,
    },
    "Chicago, US": {
        "lat": 41.8781,
        "lon": -87.6298,
        "continent": "NA",
        "has_port": False,
        "has_airport": True,
        "has_rail": True,
    },
    "Denver, US": {
        "lat": 39.7392,
        "lon": -104.9903,
        "continent": "NA",
        "has_port": False,
        "has_airport": True,
        "has_rail": True,
    },
}

# --- 2. GERÇEKÇİ LOJİSTİK PARAMETRELERİ VE HESAPLAMA FAKTÖRLERİ ---
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
        "affected_regions": [
            ("EU", "NA"),
            ("AS", "NA"),
            ("ME", "NA"),
            ("EU", "SA"),
        ],
        "detour_km": 5200,
        "detour_days": 9.5,
        "cost_penalty": 3100,
    },
    "Suez Canal (Egypt)": {
        "affected_regions": [("EU", "AS"), ("AS", "EU"), ("EU", "ME")],
        "detour_km": 6500,
        "detour_days": 11.5,
        "cost_penalty": 3500,
    },
    "Panama Canal (Panama)": {
        "affected_regions": [("NA", "AS"), ("AS", "NA"), ("EU", "NA")],
        "detour_km": 8000,
        "detour_days": 14.0,
        "cost_penalty": 4500,
    },
    "Strait of Malacca (SG/ID/MY)": {
        "affected_regions": [("AS", "EU"), ("AS", "ME")],
        "detour_km": 3000,
        "detour_days": 5.0,
        "cost_penalty": 1800,
    },
    "Bab el-Mandeb (Red Sea)": {
        "affected_regions": [("EU", "AS"), ("AS", "EU")],
        "detour_km": 6000,
        "detour_days": 10.0,
        "cost_penalty": 2900,
    },
    "Strait of Hormuz (Persian Gulf)": {
        "affected_regions": [("ME", "AS"), ("ME", "EU")],
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


# --- 3. DİNAMİK ALTYAPI VE KRİZ KONTROL DİZGELERİ ---
def get_infrastructure_supported_modes(origin, destination):
    """Liman/Havalimanı varlığı ve karasal kesintisizliğe göre kullanılabilir modları dinamik filtreler."""
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

    # 1. Hava Yolu Filtresi: İki tarafta da havalimanı şartı
    if orig["has_airport"] and dest["has_airport"]:
        feasible_modes.append("Air Freight")

    # 2. Deniz Yolu Filtresi: İki tarafta da deniz limanı şartı
    if orig["has_port"] and dest["has_port"]:
        feasible_modes.append("Sea Freight")

    # 3. Kara & Demir Yolu Filtresi: Aynı kıtada olmalı (kesintisiz karasal hat)
    if orig["continent"] == dest["continent"]:
        if orig["has_rail"] and dest["has_rail"]:
            feasible_modes.append("Rail Freight")
        feasible_modes.append("Road Freight")

    return feasible_modes


def calculate_chokepoint_impact(
    origin, destination, mode, blocked_chokepoints
):
    """Seçilen Boğaz/Kanal kapalıysa deniz rotasına sapma ve maliyet cezası hesaplar."""
    if "Sea" not in mode or not blocked_chokepoints:
        return 0, 0, 0, False

    orig_cont = GLOBAL_HUBS_DB.get(origin, {}).get("continent", "EU")
    dest_cont = GLOBAL_HUBS_DB.get(destination, {}).get("continent", "NA")

    total_extra_km = 0
    total_extra_days = 0
    total_extra_cost = 0
    is_affected = False

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


def generate_multimodal_routes(origin, destination):
    """Aktarmalı Multimodal rotalar üretir."""
    orig_info = GLOBAL_HUBS_DB[origin]
    dest_info = GLOBAL_HUBS_DB[destination]

    hub_name = "Rotterdam, NL" if origin != "Rotterdam, NL" else "Istanbul, TR"
    if hub_name == destination:
        hub_name = "Hamburg, DE"
    hub_info = GLOBAL_HUBS_DB[hub_name]

    d1 = haversine(
        orig_info["lat"], orig_info["lon"], hub_info["lat"], hub_info["lon"]
    )
    d2 = haversine(
        hub_info["lat"], hub_info["lon"], dest_info["lat"], dest_info["lon"]
    )
    total_dist = (d1 * 1.3) + (d2 * 1.3)

    cost = (d1 * 0.55) + (d2 * 0.25) + 400.0
    days = (d1 / (60 * 24)) + (d2 / (25 * 24)) + 3.0

    return pd.DataFrame([{
        "Shipment_ID": (
            f"MULTI-{origin[:3]}-{hub_name[:3]}-{destination[:3]}".upper()
        ),
        "Origin_Name": origin,
        "Origin_Lat": orig_info["lat"],
        "Origin_Lon": orig_info["lon"],
        "Destination_Name": destination,
        "Destination_Lat": dest_info["lat"],
        "Destination_Lon": dest_info["lon"],
        "Hub_Name": hub_name,
        "Hub_Lat": hub_info["lat"],
        "Hub_Lon": hub_info["lon"],
        "Transport_Mode": f"Multimodal (Trans-Hub: {hub_name.split(',')[0]})",
        "Distance_KM": round(total_dist, 1),
        "Base_Cost_USD": round(cost, 2),
        "Transit_Days": round(days, 1),
        "CO2_Emissions_Tons": round((d1 * 0.00018) + (d2 * 0.00008), 2),
        "Geopolitical_Risk": "Low",
        "Weather_Condition": "Clear",
        "Port_Congestion_Index": 4.5,
        "Delay_Days": 1.0,
    }])


# --- 4. VERİ SİSTEMİ ---
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
st.sidebar.header("📍 Route Selection")

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

# --- 6. HESAPLAMA MOTORU ---
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

# Multimodal Opsiyon Ekleme
mm_df = generate_multimodal_routes(selected_origin, selected_dest)
if not mm_df.empty:
    route_candidates = pd.concat(
        [route_candidates, mm_df], ignore_index=True
    )

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

st.divider()

# --- PANEL 3: HARİTA GÖRSELLEŞTİRME & GRAFİKLER ---
col_left, col_right = st.columns([2, 1])

with col_left:
    st.subheader("🌐 Global Route & Chokepoint Map")
    fig = go.Figure()

    # Tüm Dünya Hub'larını Mavi Nokta Olarak Göster
    fig.add_trace(
        go.Scattergeo(
            lon=[h["lon"] for h in GLOBAL_HUBS_DB.values()],
            lat=[h["lat"] for h in GLOBAL_HUBS_DB.values()],
            hovertext=list(GLOBAL_HUBS_DB.keys()),
            mode="markers",
            marker=dict(size=8, color="#1f77b4", opacity=0.7),
            name="Logistics Hubs",
        )
    )

    # Aktif Rota Çizgisi
    if "Hub_Lat" in optimal_route and pd.notnull(optimal_route.get("Hub_Lat")):
        route_lons = [
            optimal_route["Origin_Lon"],
            optimal_route["Hub_Lon"],
            optimal_route["Destination_Lon"],
        ]
        route_lats = [
            optimal_route["Origin_Lat"],
            optimal_route["Hub_Lat"],
            optimal_route["Destination_Lat"],
        ]
    else:
        route_lons = [
            optimal_route["Origin_Lon"],
            optimal_route["Destination_Lon"],
        ]
        route_lats = [
            optimal_route["Origin_Lat"],
            optimal_route["Destination_Lat"],
        ]

    fig.add_trace(
        go.Scattergeo(
            lon=route_lons,
            lat=route_lats,
            mode="lines+markers",
            line=dict(width=4, color="#ef553b"),
            marker=dict(size=12, color="#ef553b"),
            name=f"OPTIMAL ({optimal_route['Transport_Mode']})",
        )
    )

    fig.update_layout(
        geo=dict(
            projection_type="natural earth",
            showland=True,
            landcolor="rgb(240, 240, 240)",
            countrycolor="rgb(200, 200, 200)",
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

# --- PANEL 4: C-LEVEL ÖZET VE AKSİYON RAPORU ---
st.subheader("📝 Executive Summary")
if blocked_canals:
    st.warning(
        f"⚠️ **Chokepoint Active Blockage:** **{', '.join(blocked_canals)}**"
        " selected as CLOSED. Sea Freight costs & transit times updated"
        " accordingly."
    )

st.success(
    f"**Recommended Route:** **{selected_origin}** ➔ **{selected_dest}** via"
    f" **{optimal_route['Transport_Mode']}** | Total Freight Cost:"
    f" **${optimal_route['Base_Cost_USD']:,.2f}** | Total ETA:"
    f" **{total_eta} days**."
)
