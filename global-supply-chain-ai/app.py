import os
import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from optimizer import DelayPredictor, optimize_supply_chain
from data_generator import generate_global_logistics_data, haversine, HUBS

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_PATH = os.path.join(BASE_DIR, "global_logistics_data.csv")

st.set_page_config(
    page_title="Global Supply Chain Resilience Engine", 
    layout="wide", 
    page_icon="🌍"
)

st.title("🌍 Global Multi-Modal Supply Chain Resilience & ESG Engine")
st.markdown("**Enterprise AI Platform** | Real-Time Route Optimization, ML Delay Forecasting & Emissions Control")
st.divider()

# Veri Yükleme
@st.cache_data
def load_data():
    if os.path.exists(DATA_PATH):
        df_loaded = pd.read_csv(DATA_PATH)
        # Eğer veri 200 hub'lı yeni yapı değilse yeniden üret
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

# ML Modelini Eğitme
@st.cache_resource
def get_trained_model(dataframe):
    predictor = DelayPredictor()
    predictor.train(dataframe)
    return predictor

predictor = get_trained_model(df)

# Tüm 200 Hub Listesi
all_hub_names = sorted(list(set(df["Origin_Name"].unique()).union(set(df["Destination_Name"].unique()))))

# --- SIDEBAR: ÖZELLEŞTİRİLMİŞ BÖLGE VE C-LEVEL STRATEJİ KONTROLLERİ ---
st.sidebar.header("📍 Route Selection (Nereden ➡️ Nereye)")

# 1. Çıkış ve Varış Bölgesi Seçimi
default_origin_idx = all_hub_names.index("Istanbul, TR") if "Istanbul, TR" in all_hub_names else 0
default_dest_idx = all_hub_names.index("Rotterdam, NL") if "Rotterdam, NL" in all_hub_names else 1

selected_origin = st.sidebar.selectbox("1. Çıkış Bölgesi (Origin):", options=all_hub_names, index=default_origin_idx)

# Varış bölgesinden çıkış bölgesini çıkar
dest_options = [h for h in all_hub_names if h != selected_origin]
selected_dest = st.sidebar.selectbox("2. Varış Bölgesi (Destination):", options=dest_options, index=0)

st.sidebar.divider()
st.sidebar.header("🎯 C-Level Strategy Controls")

cost_weight = st.sidebar.slider("💰 Cost Priority (%)", 0.0, 1.0, 0.4, 0.05)
time_weight = st.sidebar.slider("⏱️ Transit & Delay Priority (%)", 0.0, 1.0, 0.3, 0.05)
co2_weight = st.sidebar.slider("🌱 CO2 Emission Priority (%)", 0.0, 1.0, 0.3, 0.05)

st.sidebar.divider()
st.sidebar.subheader("Crisis Scenario Simulation")
risk_filter = st.sidebar.multiselect(
    "Active Geopolitical Risk Filter:",
    options=df["Geopolitical_Risk"].unique(),
    default=df["Geopolitical_Risk"].unique()
)

# --- İLGİLİ ROTALARI FİLTRELEME VEYA ANLIK OLUŞTURMA ---
route_candidates = df[(df["Origin_Name"] == selected_origin) & (df["Destination_Name"] == selected_dest)].copy()
route_candidates = route_candidates[route_candidates["Geopolitical_Risk"].isin(risk_filter)].reset_index(drop=True)

# Seçilen iki nokta arasında hazır rota yoksa dinamik olarak hesapla
if route_candidates.empty:
    orig_info = next(h for h in HUBS if h["name"] == selected_origin)
    dest_info = next(h for h in HUBS if h["name"] == selected_dest)
    dist_km = haversine(orig_info["lat"], orig_info["lon"], dest_info["lat"], dest_info["lon"])

    modes = ["Air Freight", "Sea Freight", "Rail Freight", "Road Freight"]
    dyn_rows = []
    for m in modes:
        if m == "Air Freight": c, s, co2 = 2.1, 750, 0.0006
        elif m == "Sea Freight": c, s, co2 = 0.25, 35, 0.00008
        elif m == "Rail Freight": c, s, co2 = 0.55, 60, 0.00018
        else: c, s, co2 = 0.95, 70, 0.00035

        dyn_rows.append({
            "Shipment_ID": f"DYN-{selected_origin[:3]}-{selected_dest[:3]}-{m[:2]}".upper(),
            "Origin_Name": selected_origin, "Origin_Lat": orig_info["lat"], "Origin_Lon": orig_info["lon"],
            "Destination_Name": selected_dest, "Destination_Lat": dest_info["lat"], "Destination_Lon": dest_info["lon"],
            "Transport_Mode": m, "Distance_KM": round(dist_km, 1),
            "Base_Cost_USD": round(dist_km * c, 2),
            "Transit_Days": round(dist_km / (s * 24), 1) if round(dist_km / (s * 24), 1) > 0.5 else 0.5,
            "CO2_Emissions_Tons": round(dist_km * co2, 2),
            "Geopolitical_Risk": "Low", "Weather_Condition": "Clear", "Port_Congestion_Index": 5.0, "Delay_Days": 1.0
        })
    route_candidates = pd.DataFrame(dyn_rows)

# Optimizasyonu Çalıştır
optimal_route = optimize_supply_chain(route_candidates, cost_weight, time_weight, co2_weight)

# --- PANEL 1: SEÇİLEN ROTA KARTI ---
st.subheader("📍 Active Selected Corridor & Detailed Breakdown")
st.markdown(f"### 🚀 **{selected_origin}** ➡️ **{selected_dest}**")

total_eta = round(optimal_route['Transit_Days'] + optimal_route['Delay_Days'], 1)

m_col1, m_col2, m_col3, m_col4, m_col5 = st.columns(5)
m_col1.metric("Selected Route ID", optimal_route["Shipment_ID"])
m_col2.metric("Optimal Mode", optimal_route["Transport_Mode"])
m_col3.metric("Base Transit Time", f"{optimal_route['Transit_Days']} Days")
m_col4.metric("AI Predicted Delay", f"+{optimal_route['Delay_Days']} Days")
m_col5.metric("Total Estimated ETA", f"{total_eta} Days", delta=f"{optimal_route['Delay_Days']} Days Delay", delta_color="inverse")

st.divider()

# --- PANEL 2: BENCHMARK TABLOSU ---
st.subheader("⚖️ Strategic Scenario Benchmark for Selected Route")
st.caption("Seçtiğiniz bu koridorda farklı stratejilere göre yapay zeka tarafından önerilen taşıma modları:")

pure_cost_route = optimize_supply_chain(route_candidates, cost_weight=1.0, time_weight=0.0, co2_weight=0.0)
pure_time_route = optimize_supply_chain(route_candidates, cost_weight=0.0, time_weight=1.0, co2_weight=0.0)
pure_co2_route  = optimize_supply_chain(route_candidates, cost_weight=0.0, time_weight=0.0, co2_weight=1.0)

comparison_data = [
    {
        "Strategy": "🎯 CEO Strategy (Selected Weights)",
        "Mode": optimal_route["Transport_Mode"],
        "Total Cost ($)": f"${optimal_route['Base_Cost_USD']:,.2f}",
        "Total ETA": f"{total_eta} Days",
        "CO2 Footprint": f"{optimal_route['CO2_Emissions_Tons']} Tons"
    },
    {
        "Strategy": "💵 Pure Cost Optimization (Lowest Price)",
        "Mode": pure_cost_route["Transport_Mode"],
        "Total Cost ($)": f"${pure_cost_route['Base_Cost_USD']:,.2f}",
        "Total ETA": f"{round(pure_cost_route['Transit_Days'] + pure_cost_route['Delay_Days'], 1)} Days",
        "CO2 Footprint": f"{pure_cost_route['CO2_Emissions_Tons']} Tons"
    },
    {
        "Strategy": "⚡ Fastest Delivery (Minimum Transit Time)",
        "Mode": pure_time_route["Transport_Mode"],
        "Total Cost ($)": f"${pure_time_route['Base_Cost_USD']:,.2f}",
        "Total ETA": f"{round(pure_time_route['Transit_Days'] + pure_time_route['Delay_Days'], 1)} Days",
        "CO2 Footprint": f"{pure_time_route['CO2_Emissions_Tons']} Tons"
    },
    {
        "Strategy": "🌱 Green / Low Emission (ESG Optimization)",
        "Mode": pure_co2_route["Transport_Mode"],
        "Total Cost ($)": f"${pure_co2_route['Base_Cost_USD']:,.2f}",
        "Total ETA": f"{round(pure_co2_route['Transit_Days'] + pure_co2_route['Delay_Days'], 1)} Days",
        "CO2 Footprint": f"{pure_co2_route['CO2_Emissions_Tons']} Tons"
    }
]
st.table(pd.DataFrame(comparison_data))

st.divider()

# --- PANEL 3: CANLI DÜNYA HARİTASI VE ÇİZGİ ROTA ---
col_left, col_right = st.columns([2, 1])

with col_left:
    st.subheader("🌐 Trajectory Map Visualizer")
    
    fig = go.Figure()

    # Tüm 200 Hub Noktası (Gri)
    fig.add_trace(go.Scattergeo(
        lon = df['Origin_Lon'].tolist(),
        lat = df['Origin_Lat'].tolist(),
        hovertext = df['Origin_Name'].tolist(),
        mode = 'markers',
        marker = dict(size=5, color='gray', opacity=0.4),
        name = "Global Logistics Hubs (200+)"
    ))

    # Mod Stilleri
    mode_styles = {
        "Air Freight": {"color": "#ef553b", "dash": "dash", "width": 3},
        "Sea Freight": {"color": "#00cc96", "dash": "solid", "width": 5},
        "Rail Freight": {"color": "#ab63fa", "dash": "dot", "width": 4},
        "Road Freight": {"color": "#ffa15a", "dash": "solid", "width": 4}
    }

    opt_mode = optimal_route["Transport_Mode"]
    style = mode_styles.get(opt_mode, {"color": "red", "dash": "solid", "width": 4})

    # Seçilen Rotayı Çiz
    fig.add_trace(go.Scattergeo(
        lon = [optimal_route["Origin_Lon"], optimal_route["Destination_Lon"]],
        lat = [optimal_route["Origin_Lat"], optimal_route["Destination_Lat"]],
        mode = 'lines+markers',
        line = dict(width=style["width"], color=style["color"], dash=style["dash"]),
        marker = dict(size=12, color=style["color"]),
        name = f"OPTIMAL ROUTE: {selected_origin} ➡️ {selected_dest} ({opt_mode})"
    ))

    fig.update_layout(
        geo = dict(
            projection_type = 'natural earth',
            showland = True,
            landcolor = 'rgb(240, 240, 240)',
            countrycolor = 'rgb(200, 200, 200)'
        ),
        margin = dict(l=0, r=0, t=30, b=0),
        height = 450
    )
    st.plotly_chart(fig, use_container_width=True)

with col_right:
    st.subheader("📊 Modal Cost & Transit Trade-Off")
    fig_bar = px.bar(
        route_candidates,
        x="Transport_Mode",
        y="Base_Cost_USD",
        color="Transport_Mode",
        title="Candidate Cost Comparison ($)"
    )
    st.plotly_chart(fig_bar, use_container_width=True)

st.divider()

# --- PANEL 4: ANLIK GECİKME TAHMİNİ ---
st.subheader("🤖 Real-Time ML Delay Predictor")

p_col1, p_col2, p_col3, p_col4 = st.columns(4)
mode_input = p_col1.selectbox("Transport Mode", df["Transport_Mode"].unique())
weather_input = p_col2.selectbox("Weather Condition", df["Weather_Condition"].unique())
geo_input = p_col3.selectbox("Geopolitical Risk Level", df["Geopolitical_Risk"].unique())
dist_input = p_col4.number_input("Distance (KM)", 100, 25000, int(optimal_route["Distance_KM"]))

sample_to_predict = {
    "Transport_Mode": mode_input,
    "Weather_Condition": weather_input,
    "Geopolitical_Risk": geo_input,
    "Distance_KM": dist_input,
    "Port_Congestion_Index": 6.5
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
    f"Connecting **{selected_origin}** to **{selected_dest}** under operational weights (Cost: **{c_pct}%**, Time: **{t_pct}%**, CO2: **{co2_pct}%**), "
    f"the engine selects **{optimal_route['Shipment_ID']}** via **{optimal_route['Transport_Mode']}**.\n\n"
    f"- **Distance & Cost:** Distance of **{optimal_route['Distance_KM']} KM** with total base cost **${optimal_route['Base_Cost_USD']:,.2f}**.\n"
    f"- **ETA & Reliability:** Base transit time **{optimal_route['Transit_Days']} days** + **{optimal_route['Delay_Days']} days predicted delay** (Total ETA: **{total_eta} Days**).\n"
    f"- **ESG Impact:** Estimated carbon footprint of **{optimal_route['CO2_Emissions_Tons']} Tons**."
)
st.success(summary_text)
