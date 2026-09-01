import os
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
from data_generator import HUBS, generate_global_logistics_data, haversine
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

# --- 1. KÜRESEL AKTARMA HUBLARI VE UYGUNLUK FİLTRELERİ ---
GLOBAL_TRANSSHIPMENT_HUBS = [
    "Rotterdam, NL",
    "Hamburg, DE",
    "Shanghai, CN",
    "Singapore, SG",
    "Dubai, AE",
    "Istanbul, TR",
    "Los Angeles, US",
    "New York, US",
    "Antwerp, BE",
    "Busan, KR",
]


def is_north_america(hub_name):
    """Kuzey Amerika liman/şehirlerini algılar."""
    na_codes = [", US", ", CA", ", MX"]
    return any(hub_name.endswith(code) for code in na_codes)


def get_feasible_modes(origin, destination):
    """Direkt (tek modlu) rotalarda fiziksel imkansız modları engeller."""
    orig_is_na = is_north_america(origin)
    dest_is_na = is_north_america(destination)

    # Okyanus aşırı direkt geçişlerde sadece Deniz ve Hava yolu geçerlidir
    if orig_is_na != dest_is_na:
        return ["Air Freight", "Sea Freight"]

    return ["Air Freight", "Sea Freight", "Rail Freight", "Road Freight"]


def find_best_transshipment_hub(origin, destination):
    """Origin ve Destination arasındaki en optimum aktarma hub'ını dinamik seçer."""
    orig_info = next(
        (h for h in HUBS if h["name"] == origin), {"lat": 41.0, "lon": 28.9}
    )
    dest_info = next(
        (h for h in HUBS if h["name"] == destination),
        {"lat": 40.7, "lon": -74.0},
    )

    candidates = [
        h
        for h in GLOBAL_TRANSSHIPMENT_HUBS
        if h != origin and h != destination
    ]
    if not candidates:
        candidates = [
            h["name"]
            for h in HUBS
            if h["name"] != origin and h["name"] != destination
        ][:5]

    best_hub = None
    min_dist = float("inf")

    for hub_name in candidates:
        hub_info = next((h for h in HUBS if h["name"] == hub_name), None)
        if not hub_info:
            continue
        d1 = haversine(
            orig_info["lat"], orig_info["lon"], hub_info["lat"], hub_info["lon"]
        )
        d2 = haversine(
            hub_info["lat"], hub_info["lon"], dest_info["lat"], dest_info["lon"]
        )
        if (d1 + d2) < min_dist:
            min_dist = d1 + d2
            best_hub = hub_name

    return best_hub if best_hub else "Rotterdam, NL"


def generate_multimodal_routes(origin, destination):
    """DÜNYADAKİ HER YER İÇİN dinamik Multimodal (Karma) Rotalar üretir."""
    hub_name = find_best_transshipment_hub(origin, destination)

    orig_info = next(h for h in HUBS if h["name"] == origin)
    hub_info = next(h for h in HUBS if h["name"] == hub_name)
    dest_info = next(h for h in HUBS if h["name"] == destination)

    dist_leg1 = haversine(
        orig_info["lat"], orig_info["lon"], hub_info["lat"], hub_info["lon"]
    )
    dist_leg2 = haversine(
        hub_info["lat"], hub_info["lon"], dest_info["lat"], dest_info["lon"]
    )
    total_dist = dist_leg1 + dist_leg2

    orig_is_na = is_north_america(origin)
    dest_is_na = is_north_america(destination)
    hub_is_na = is_north_america(hub_name)

    multimodal_candidates = []

    # Senaryo A: Karasal/Demiryolu ➔ Hub ➔ Deniz/Havayolu (Veya tersi)
    leg1_mode = "Rail Freight" if orig_is_na == hub_is_na else "Sea Freight"
    leg2_mode = "Sea Freight" if hub_is_na != dest_is_na else "Rail Freight"

    if leg1_mode == "Rail Freight" and leg2_mode == "Rail Freight":
        leg2_mode = "Road Freight"  # Çeşitlilik sağla

    # Birim maliyet ve süre katsayıları
    rates = {
        "Air Freight": (2.1, 750, 0.0006),
        "Sea Freight": (0.25, 35, 0.00008),
        "Rail Freight": (0.55, 60, 0.00018),
        "Road Freight": (0.95, 70, 0.00035),
    }

    c1, s1, co1 = rates[leg1_mode]
    c2, s2, co2 = rates[leg2_mode]

    cost = (dist_leg1 * c1) + (dist_leg2 * c2) + 350.0  # +$350 Aktarma Liman Ücreti
    days = (dist_leg1 / (s1 * 24)) + (
        dist_leg2 / (s2 * 24)
    ) + 1.2  # +1.2 Gün Liman Aktarma Süresi
    co2_total = (dist_leg1 * co1) + (dist_leg2 * co2)

    mode_label = (
        f"Multimodal ({leg1_mode.split()[0]} ➔ {hub_name.split(',')[0]} ➔"
        f" {leg2_mode.split()[0]})"
    )

    multimodal_candidates.append({
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
        "Transport_Mode": mode_label,
        "Distance_KM": round(total_dist, 1),
        "Base_Cost_USD": round(cost, 2),
        "Transit_Days": round(days, 1) if round(days, 1) > 0.5 else 0.5,
        "CO2_Emissions_Tons": round(co2_total, 2),
        "Geopolitical_Risk": "Low",
        "Weather_Condition": "Clear",
        "Port_Congestion_Index": 5.0,
        "Delay_Days": 1.2,
    })

    return pd.DataFrame(multimodal_candidates)


# --- 2. VERİ VE MODEL YÜKLEME ---
@st.cache_data
def load_data():
    if os.path.exists(DATA_PATH):
        df_loaded = pd.read_csv(DATA_PATH)
        if len(df_loaded["Origin_Name"].unique()) < 100:
            df_gen = generate_global_logistics_data()
            df_gen.to_csv(DATA_PATH, index=False)
            return df_gen
        return df_loaded
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

all_hub_names = sorted(
    list(
        set(df["Origin_Name"].unique()).union(
            set(df["Destination_Name"].unique())
        )
    )
)

# --- 3. SIDEBAR: KULLANICI SEÇİMLERİ ---
st.sidebar.header("📍 Route Selection (Nereden ➡️ Nereye)")

default_origin_idx = (
    all_hub_names.index("Istanbul, TR") if "Istanbul, TR" in all_hub_names else 0
)
selected_origin = st.sidebar.selectbox(
    "1. Çıkış Bölgesi (Origin):",
    options=all_hub_names,
    index=default_origin_idx,
)

dest_options = [h for h in all_hub_names if h != selected_origin]
selected_dest = st.sidebar.selectbox(
    "2. Varış Bölgesi (Destination):", options=dest_options, index=0
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
st.sidebar.subheader("Crisis Scenario Simulation")
risk_filter = st.sidebar.multiselect(
    "Active Geopolitical Risk Filter:",
    options=df["Geopolitical_Risk"].unique(),
    default=df["Geopolitical_Risk"].unique(),
)

# --- 4. ROTA VE MOD FİLTRELEME & DİNAMİK MULTIMODAL EKLEME ---
feasible_modes = get_feasible_modes(selected_origin, selected_dest)

route_candidates = df[
    (df["Origin_Name"] == selected_origin)
    & (df["Destination_Name"] == selected_dest)
    & (df["Transport_Mode"].isin(feasible_modes))
    & (df["Geopolitical_Risk"].isin(risk_filter))
].reset_index(drop=True)

# Seçilen noktalar arası veri yoksa tekli modları üret
if route_candidates.empty:
    orig_info = next(h for h in HUBS if h["name"] == selected_origin)
    dest_info = next(h for h in HUBS if h["name"] == selected_dest)
    dist_km = haversine(
        orig_info["lat"], orig_info["lon"], dest_info["lat"], dest_info["lon"]
    )

    dyn_rows = []
    for m in feasible_modes:
        if m == "Air Freight":
            c, s, co2 = 2.1, 750, 0.0006
        elif m == "Sea Freight":
            c, s, co2 = 0.25, 35, 0.00008
        elif m == "Rail Freight":
            c, s, co2 = 0.55, 60, 0.00018
        else:
            c, s, co2 = 0.95, 70, 0.00035

        transit_days = (
            round(dist_km / (s * 24), 1)
            if round(dist_km / (s * 24), 1) > 0.5
            else 0.5
        )

        dyn_rows.append({
            "Shipment_ID": (
                f"DYN-{selected_origin[:3]}-{selected_dest[:3]}-{m[:2]}".upper()
            ),
            "Origin_Name": selected_origin,
            "Origin_Lat": orig_info["lat"],
            "Origin_Lon": orig_info["lon"],
            "Destination_Name": selected_dest,
            "Destination_Lat": dest_info["lat"],
            "Destination_Lon": dest_info["lon"],
            "Transport_Mode": m,
            "Distance_KM": round(dist_km, 1),
            "Base_Cost_USD": round(dist_km * c, 2),
            "Transit_Days": transit_days,
            "CO2_Emissions_Tons": round(dist_km * co2, 2),
            "Geopolitical_Risk": "Low",
            "Weather_Condition": "Clear",
            "Port_Congestion_Index": 5.0,
            "Delay_Days": 1.0,
        })
    route_candidates = pd.DataFrame(dyn_rows)

# HER YER İÇİN MULTIMODAL ALTERNATİFİ EKLE
mm_df = generate_multimodal_routes(selected_origin, selected_dest)
if not mm_df.empty:
    route_candidates = pd.concat(
        [route_candidates, mm_df], ignore_index=True
    )

# Optimizasyonu Çalıştır
optimal_route = optimize_supply_chain(
    route_candidates, cost_weight, time_weight, co2_weight
)

# --- PANEL 1: SEÇİLEN ROTA KARTI ---
st.subheader("📍 Active Selected Corridor & Detailed Breakdown")
st.markdown(f"### 🚀 **{selected_origin}** ➡️ **{selected_dest}**")

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

# --- PANEL 2: BENCHMARK TABLOSU ---
st.subheader("⚖️ Strategic Scenario Benchmark for Selected Route")
st.caption(
    "Seçtiğiniz bu koridorda farklı stratejilere göre yapay zeka tarafından"
    " önerilen taşıma modları (Multimodal Dahil):"
)

pure_cost_route = optimize_supply_chain(
    route_candidates, cost_weight=1.0, time_weight=0.0, co2_weight=0.0
)
pure_time_route = optimize_supply_chain(
    route_candidates, cost_weight=0.0, time_weight=1.0, co2_weight=0.0
)
pure_co2_route = optimize_supply_chain(
    route_candidates, cost_weight=0.0, time_weight=0.0, co2_weight=1.0
)

comparison_data = [
    {
        "Strategy": "🎯 CEO Strategy (Selected Weights)",
        "Mode": optimal_route["Transport_Mode"],
        "Total Cost ($)": f"${optimal_route['Base_Cost_USD']:,.2f}",
        "Total ETA": f"{total_eta} Days",
        "CO2 Footprint": f"{optimal_route['CO2_Emissions_Tons']} Tons",
    },
    {
        "Strategy": "💵 Pure Cost Optimization (Lowest Price)",
        "Mode": pure_cost_route["Transport_Mode"],
        "Total Cost ($)": f"${pure_cost_route['Base_Cost_USD']:,.2f}",
        "Total ETA": (
            f"{round(pure_cost_route['Transit_Days'] + pure_cost_route['Delay_Days'], 1)} Days"
        ),
        "CO2 Footprint": f"{pure_cost_route['CO2_Emissions_Tons']} Tons",
    },
    {
        "Strategy": "⚡ Fastest Delivery (Minimum Transit Time)",
        "Mode": pure_time_route["Transport_Mode"],
        "Total Cost ($)": f"${pure_time_route['Base_Cost_USD']:,.2f}",
        "Total ETA": (
            f"{round(pure_time_route['Transit_Days'] + pure_time_route['Delay_Days'], 1)} Days"
        ),
        "CO2 Footprint": f"{pure_time_route['CO2_Emissions_Tons']} Tons",
    },
    {
        "Strategy": "🌱 Green / Low Emission (ESG Optimization)",
        "Mode": pure_co2_route["Transport_Mode"],
        "Total Cost ($)": f"${pure_co2_route['Base_Cost_USD']:,.2f}",
        "Total ETA": (
            f"{round(pure_co2_route['Transit_Days'] + pure_co2_route['Delay_Days'], 1)} Days"
        ),
        "CO2 Footprint": f"{pure_co2_route['CO2_Emissions_Tons']} Tons",
    },
]
st.table(pd.DataFrame(comparison_data))

st.divider()

# --- PANEL 3: HARİTA VE MOD GRAFİĞİ ---
col_left, col_right = st.columns([2, 1])

with col_left:
    st.subheader("🌐 Trajectory Map Visualizer")
    fig = go.Figure()

    # Tüm Hub Noktaları
    fig.add_trace(
        go.Scattergeo(
            lon=df["Origin_Lon"].tolist(),
            lat=df["Origin_Lat"].tolist(),
            hovertext=df["Origin_Name"].tolist(),
            mode="markers",
            marker=dict(size=5, color="gray", opacity=0.4),
            name="Global Logistics Hubs (200+)",
        )
    )

    # Rota Koordinatları (Multimodal ise Hub üzerinden geçer)
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
        route_label = (
            f"OPTIMAL MULTIMODAL ROUTE: {selected_origin} ➔"
            f" {optimal_route['Hub_Name']} ➔ {selected_dest}"
        )
    else:
        route_lons = [
            optimal_route["Origin_Lon"],
            optimal_route["Destination_Lon"],
        ]
        route_lats = [
            optimal_route["Origin_Lat"],
            optimal_route["Destination_Lat"],
        ]
        route_label = (
            f"OPTIMAL ROUTE: {selected_origin} ➡️ {selected_dest}"
            f" ({optimal_route['Transport_Mode']})"
        )

    fig.add_trace(
        go.Scattergeo(
            lon=route_lons,
            lat=route_lats,
            mode="lines+markers",
            line=dict(width=4, color="#ab63fa", dash="dashdot"),
            marker=dict(size=10, color="#ef553b"),
            name=route_label,
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
    st.subheader("📊 Modal Cost & Transit Trade-Off")
    fig_bar = px.bar(
        route_candidates,
        x="Transport_Mode",
        y="Base_Cost_USD",
        color="Transport_Mode",
        title="Candidate Cost Comparison ($)",
    )
    st.plotly_chart(fig_bar, use_container_width=True)

st.divider()

# --- PANEL 4: ANLIK GECİKME TAHMİNİ ---
st.subheader("🤖 Real-Time ML Delay Predictor")

available_predict_modes = route_candidates["Transport_Mode"].tolist()
p_col1, p_col2, p_col3, p_col4 = st.columns(4)
mode_input = p_col1.selectbox("Transport Mode", available_predict_modes)
weather_input = p_col2.selectbox(
    "Weather Condition", df["Weather_Condition"].unique()
)
geo_input = p_col3.selectbox(
    "Geopolitical Risk Level", df["Geopolitical_Risk"].unique()
)
dist_input = p_col4.number_input(
    "Distance (KM)", 100, 25000, int(optimal_route["Distance_KM"])
)

sample_to_predict = {
    "Transport_Mode": (
        mode_input if "Multimodal" not in mode_input else "Rail Freight"
    ),
    "Weather_Condition": weather_input,
    "Geopolitical_Risk": geo_input,
    "Distance_KM": dist_input,
    "Port_Congestion_Index": 6.5,
}
pred_delay = predictor.predict_delay(sample_to_predict)
st.info(f"💡 **AI Model Predicted Delay:** {pred_delay} Days for custom setup.")

st.divider()

# --- PANEL 5: C-LEVEL ÖZET ---
st.subheader("📝 Executive Briefing (Automated C-Level Summary)")

c_pct = int(cost_weight * 100)
t_pct = int(time_weight * 100)
co2_pct = int(co2_weight * 100)

summary_text = (
    f"**Strategic AI Recommendation:**\n"
    f"Connecting **{selected_origin}** to **{selected_dest}** under operational"
    f" weights (Cost: **{c_pct}%**, Time: **{t_pct}%**, CO2: **{co2_pct}%**),"
    f" the engine selects **{optimal_route['Shipment_ID']}** via"
    f" **{optimal_route['Transport_Mode']}**.\n\n"
    f"- **Distance & Cost:** Total journey of **{optimal_route['Distance_KM']}"
    f" KM** with total estimated base cost"
    f" **${optimal_route['Base_Cost_USD']:,.2f}**.\n"
    f"- **ETA & Reliability:** Base transit time **{optimal_route['Transit_Days']}"
    f" days** + **{optimal_route['Delay_Days']} days predicted delay** (Total"
    f" ETA: **{total_eta} Days**).\n"
    f"- **ESG Impact:** Estimated carbon footprint of"
    f" **{optimal_route['CO2_Emissions_Tons']} Tons**."
)
st.success(summary_text)
