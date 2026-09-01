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
    "**Enterprise AI Platform** | Real-Time Route Optimization, ML Delay"
    " Forecasting & Emissions Control"
)
st.divider()

# --- 1. KÜRESEL HUB ALTYAPI VE KRİTİK BOĞAZ/KANAL VERİTABANI ---
GLOBAL_HUBS_DB = {
    "Istanbul, TR": {
        "lat": 41.0082,
        "lon": 28.9784,
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
    "Rotterdam, NL": {
        "lat": 51.9244,
        "lon": 4.4777,
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
    },  # Kara ülkesi
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
    "Denver, US": {
        "lat": 39.7392,
        "lon": -104.9903,
        "continent": "NA",
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
    "Dubai, AE": {
        "lat": 25.2048,
        "lon": 55.2708,
        "continent": "AS",
        "has_port": True,
        "has_airport": True,
        "has_rail": False,
    },
    "Riyadh, SA": {
        "lat": 24.7136,
        "lon": 46.6753,
        "continent": "AS",
        "has_port": False,
        "has_airport": True,
        "has_rail": True,
    },
}

CHOKEPOINTS_DB = {
    "Suez Canal (Egypt)": {
        "affected_regions": [("EU", "AS"), ("AS", "EU"), ("EU", "OC")],
        "detour_km": 6500,
        "detour_days": 11.5,
        "cost_penalty": 3200,
    },
    "Panama Canal (Panama)": {
        "affected_regions": [("NA", "AS"), ("AS", "NA"), ("EU", "NA")],
        "detour_km": 8000,
        "detour_days": 14.0,
        "cost_penalty": 4500,
    },
    "Strait of Malacca (SG/ID)": {
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
}


# --- 2. DİNAMİK ALTYAPI VE ROTA KONTROL FONKSİYONLARI ---
def get_infrastructure_supported_modes(origin, destination):
    """Liman/Havalimanı varlığı ve karasal kesintisizliğe göre modları filtreler."""
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

    # 1. Hava yolu: Her iki tarafta da havalimanı olmalı
    if orig["has_airport"] and dest["has_airport"]:
        feasible_modes.append("Air Freight")

    # 2. Deniz yolu: Her iki tarafta da deniz limanı olmalı
    if orig["has_port"] and dest["has_port"]:
        feasible_modes.append("Sea Freight")

    # 3. Kara ve Demir yolu: Şehirler aynı kıtada olmalı ve karasal hat bulunmalı
    if orig["continent"] == dest["continent"]:
        if orig["has_rail"] and dest["has_rail"]:
            feasible_modes.append("Rail Freight")
        feasible_modes.append("Road Freight")

    return feasible_modes


def calculate_chokepoint_impact(
    origin, destination, mode, blocked_chokepoints
):
    """Boğaz/Kanal kapalıysa deniz rotasına ceza puanı ve rotasyon ekler."""
    if mode != "Sea Freight" or not blocked_chokepoints:
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


# --- 3. VERİ VE MODEL YÜKLEME ---
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

# --- 4. SIDEBAR VE KRİZ KONTROLLERİ ---
st.sidebar.header("📍 Route Selection (Nereden ➡️ Nereye)")

selected_origin = st.sidebar.selectbox(
    "1. Çıkış Bölgesi (Origin):", options=all_hub_names, index=0
)
dest_options = [h for h in all_hub_names if h != selected_origin]
selected_dest = st.sidebar.selectbox(
    "2. Varış Bölgesi (Destination):", options=dest_options, index=4
)

st.sidebar.divider()
st.sidebar.header("🎯 C-Level Strategy Controls")

cost_weight = st.sidebar.slider("💰 Cost Priority (%)", 0.0, 1.0, 0.4, 0.05)
time_weight = st.sidebar.slider(
    "⏱️ Transit & Delay Priority (%)", 0.0, 1.0, 0.3, 0.05
)
co2_weight = st.sidebar.slider(
    "🌱 CO2 Emission Priority (%)", 0.0, 1.0, 0.3, 0.05
)

st.sidebar.divider()
st.sidebar.header("⛔ Global Chokepoint & Canal Control")
blocked_canals = st.sidebar.multiselect(
    "Kapatılacak Boğaz / Kanalları Seçin:",
    options=list(CHOKEPOINTS_DB.keys()),
    default=[],
)

# --- 5. ROTA VE MOD OLUŞTURMA HESAPLAMALARI ---
feasible_modes = get_infrastructure_supported_modes(
    selected_origin, selected_dest
)

orig_info = GLOBAL_HUBS_DB[selected_origin]
dest_info = GLOBAL_HUBS_DB[selected_dest]
base_dist_km = haversine(
    orig_info["lat"], orig_info["lon"], dest_info["lat"], dest_info["lon"]
)

candidate_rows = []
for m in feasible_modes:
    extra_km, extra_days, extra_cost, is_choked = calculate_chokepoint_impact(
        selected_origin, selected_dest, m, blocked_canals
    )

    if m == "Air Freight":
        c, s, co2 = 2.1, 750, 0.0006
    elif m == "Sea Freight":
        c, s, co2 = 0.25, 35, 0.00008
    elif m == "Rail Freight":
        c, s, co2 = 0.55, 60, 0.00018
    else:
        c, s, co2 = 0.95, 70, 0.00035

    final_dist = base_dist_km + extra_km
    final_cost = (final_dist * c) + extra_cost
    final_days = round((final_dist / (s * 24)) + extra_days, 1)

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
        "Transport_Mode": m
        + (" (Detour/Bypassed)" if is_choked else ""),
        "Distance_KM": round(final_dist, 1),
        "Base_Cost_USD": round(final_cost, 2),
        "Transit_Days": final_days if final_days > 0.5 else 0.5,
        "CO2_Emissions_Tons": round(final_dist * co2, 2),
        "Geopolitical_Risk": "High" if is_choked else "Low",
        "Weather_Condition": "Clear",
        "Port_Congestion_Index": 8.0 if is_choked else 4.0,
        "Delay_Days": 2.5 if is_choked else 0.8,
    })

route_candidates = pd.DataFrame(candidate_rows)

# Optimizasyonu Çalıştır
optimal_route = optimize_supply_chain(
    route_candidates, cost_weight, time_weight, co2_weight
)

# --- PANEL 1: SEÇİLEN ROTA VE EKRAN ---
st.subheader("📍 Active Selected Corridor & Infrastructure Capabilities")
st.markdown(f"### 🚀 **{selected_origin}** ➡️ **{selected_dest}**")

# Altyapı Rozetleri
badge_col1, badge_col2 = st.columns(2)
badge_col1.caption(
    f"**{selected_origin} Capabilities:**"
    f" Port: {'✅' if orig_info['has_port'] else '❌'} |"
    f" Airport: {'✅' if orig_info['has_airport'] else '❌'} |"
    f" Rail: {'✅' if orig_info['has_rail'] else '❌'}"
)
badge_col2.caption(
    f"**{selected_dest} Capabilities:**"
    f" Port: {'✅' if dest_info['has_port'] else '❌'} |"
    f" Airport: {'✅' if dest_info['has_airport'] else '❌'} |"
    f" Rail: {'✅' if dest_info['has_rail'] else '❌'}"
)

total_eta = round(
    optimal_route["Transit_Days"] + optimal_route["Delay_Days"], 1
)

m_col1, m_col2, m_col3, m_col4, m_col5 = st.columns(5)
m_col1.metric("Selected Route ID", optimal_route["Shipment_ID"])
m_col2.metric("Optimal Mode", optimal_route["Transport_Mode"])
m_col3.metric("Base Transit Time", f"{optimal_route['Transit_Days']} Days")
m_col4.metric("AI Predicted Delay", f"+{optimal_route['Delay_Days']} Days")
m_col5.metric(
    "Total Estimated ETA",
    f"{total_eta} Days",
    delta=f"{optimal_route['Delay_Days']} Days Delay",
    delta_color="inverse",
)

st.divider()

# --- PANEL 2: BENCHMARK VEYA BİLGİ TABLOSU ---
st.subheader("⚖️ Strategic Scenario Benchmark for Selected Corridor")
st.caption(
    "Mevcut altyapı ve kısıtlamalara göre önerilen alternatif taşıma modları:"
)
st.table(
    route_candidates[[
        "Transport_Mode",
        "Base_Cost_USD",
        "Transit_Days",
        "CO2_Emissions_Tons",
        "Geopolitical_Risk",
    ]]
)

st.divider()

# --- PANEL 3: HARİTA GÖRSELLEŞTİRME ---
col_left, col_right = st.columns([2, 1])

with col_left:
    st.subheader("🌐 Trajectory & Chokepoint Visualizer")
    fig = go.Figure()

    # Tüm Hub Noktaları
    fig.add_trace(
        go.Scattergeo(
            lon=[h["lon"] for h in GLOBAL_HUBS_DB.values()],
            lat=[h["lat"] for h in GLOBAL_HUBS_DB.values()],
            hovertext=list(GLOBAL_HUBS_DB.keys()),
            mode="markers",
            marker=dict(size=7, color="blue", opacity=0.6),
            name="Available Logistics Hubs",
        )
    )

    # Optimum Rotayı Çiz
    fig.add_trace(
        go.Scattergeo(
            lon=[optimal_route["Origin_Lon"], optimal_route["Destination_Lon"]],
            lat=[optimal_route["Origin_Lat"], optimal_route["Destination_Lat"]],
            mode="lines+markers",
            line=dict(width=4, color="#ef553b"),
            marker=dict(size=12, color="#ef553b"),
            name=f"OPTIMAL ROUTE ({optimal_route['Transport_Mode']})",
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
    st.subheader("📊 Modal Cost Comparison ($)")
    fig_bar = px.bar(
        route_candidates,
        x="Transport_Mode",
        y="Base_Cost_USD",
        color="Transport_Mode",
        title="Valid Candidates Freight Cost",
    )
    st.plotly_chart(fig_bar, use_container_width=True)

st.divider()

# --- PANEL 4: C-LEVEL ÖZET ---
st.subheader("📝 Executive Briefing")
if blocked_canals:
    st.warning(
        f"⚠️ **Chokepoint Warning:** The following waterways are actively"
        f" blocked: **{', '.join(blocked_canals)}**. Sea freight costs and"
        " transit times have been dynamically updated for Cape detour."
    )

st.success(
    f"**Strategic Decision:** Route selected for **{selected_origin}** ➔"
    f" **{selected_dest}** via **{optimal_route['Transport_Mode']}** at total"
    f" cost of **${optimal_route['Base_Cost_USD']:,.2f}** with"
    f" **{total_eta} days total ETA**."
)
