import os
import streamlit as st
import pandas as pd
import plotly.express as px
from optimizer import DelayPredictor, optimize_supply_chain
from data_generator import generate_global_logistics_data

# Bulunulan klasörün tam yolunu dinamik olarak al
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_PATH = os.path.join(BASE_DIR, "global_logistics_data.csv")

# Streamlit Sayfa Düzenleme (Geniş Ekran)
st.set_page_config(
    page_title="Global Supply Chain Resilience Engine", 
    layout="wide", 
    page_icon="🌍"
)

# Başlık ve Alt Başlık
st.title("🌍 Global Multi-Modal Supply Chain Resilience & ESG Engine")
st.markdown("**Enterprise AI Platform** | Real-Time Route Optimization, ML Delay Forecasting & Emissions Control")
st.divider()

# Veri Yükleme (Dinamik Yol Korumalı)
@st.cache_data
def load_data():
    if os.path.exists(DATA_PATH):
        return pd.read_csv(DATA_PATH)
    else:
        # Dosya yoksa otomatik üret ve tam yola kaydet
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

# --- SIDEBAR: CEO STRATEJİ PANELİ ---
st.sidebar.header("🎯 C-Level Strategy Controls")

st.sidebar.subheader("1. Optimization Weights")
cost_weight = st.sidebar.slider("Cost Priority (%)", 0.0, 1.0, 0.4, 0.05)
time_weight = st.sidebar.slider("Transit & Delay Priority (%)", 0.0, 1.0, 0.3, 0.05)
co2_weight = st.sidebar.slider("CO2 Emission Priority (%)", 0.0, 1.0, 0.3, 0.05)

st.sidebar.divider()
st.sidebar.subheader("2. Crisis Scenario Simulation")
risk_filter = st.sidebar.multiselect(
    "Active Geopolitical Risk Filter:",
    options=df["Geopolitical_Risk"].unique(),
    default=df["Geopolitical_Risk"].unique()
)

# Veriyi Filtreleme
filtered_df = df[df["Geopolitical_Risk"].isin(risk_filter)].reset_index(drop=True)

if filtered_df.empty:
    st.error("Seçilen kriz senaryosuna uygun rota verisi bulunamadı!")
else:
    # PuLP Optimizasyon Motorunu Çalıştır
    optimal_route = optimize_supply_chain(filtered_df, cost_weight, time_weight, co2_weight)

    # --- ANA PANEL: KPI GÖSTERGELERİ ---
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Selected Optimal Route", optimal_route["Shipment_ID"])
    col2.metric("Optimal Transport Mode", optimal_route["Transport_Mode"])
    col3.metric("Total Cost", f"${optimal_route['Base_Cost_USD']:,.2f}")
    col4.metric("CO2 Footprint", f"{optimal_route['CO2_Emissions_Tons']} Tons")

    st.divider()

    # --- GRAFİKLER VE KÜRESEL HARİTA ---
    col_left, col_right = st.columns([2, 1])

    with col_left:
        st.subheader("🌐 Global Route & Risk Map Visualizer")
        fig_map = px.scatter_geo(
            filtered_df,
            lat="Origin_Lat",
            lon="Origin_Lon",
            hover_name="Origin_Name",
            size="Distance_KM",
            color="Geopolitical_Risk",
            projection="natural earth",
            title="Global Logistics Hubs & Active Risk Profiles"
        )
        st.plotly_chart(fig_map, use_container_width=True)

    with col_right:
        st.subheader("📊 Transport Mode Cost Trade-Off")
        fig_bar = px.box(
            filtered_df,
            x="Transport_Mode",
            y="Base_Cost_USD",
            color="Transport_Mode",
            title="Cost Distribution by Mode ($)"
        )
        st.plotly_chart(fig_bar, use_container_width=True)

    st.divider()

    # --- ANLIK MAKİNE ÖĞRENMESİ GECİKME TAHMİNCİSİ ---
    st.subheader("🤖 Real-Time ML Delay Predictor")
    st.caption("Parametreleri değiştirerek Makine Öğrenmesi modelinin tahmini gecikmesini test edin:")
    
    p_col1, p_col2, p_col3, p_col4 = st.columns(4)
    mode_input = p_col1.selectbox("Transport Mode", df["Transport_Mode"].unique())
    weather_input = p_col2.selectbox("Weather Condition", df["Weather_Condition"].unique())
    geo_input = p_col3.selectbox("Geopolitical Risk Level", df["Geopolitical_Risk"].unique())
    dist_input = p_col4.number_input("Distance (KM)", 1000, 20000, 8500)

    sample_to_predict = {
        "Transport_Mode": mode_input,
        "Weather_Condition": weather_input,
        "Geopolitical_Risk": geo_input,
        "Distance_KM": dist_input,
        "Port_Congestion_Index": 7.0
    }
    pred_delay = predictor.predict_delay(sample_to_predict)
    st.info(f"💡 **AI Model Predicted Delay:** {pred_delay} Days for selected operational route.")

    st.divider()

    # --- CEO YÖNETİCİ ÖZET RAPORU ---
    st.subheader("📝 Executive Briefing (Automated C-Level Summary)")
    st.success(f"""
    **Strategic AI Recommendation:**
    Based on operational constraints (Cost Weight: **{int(cost_weight*100)}%**, Time Weight: **{int(time_weight*100)}%**, CO2 Weight: **{int(co2_weight*100)}%**), 
    the engine identifies **{optimal_route['Shipment_ID']}** via **{optimal_route['Transport_Mode']}** as the optimal resilient route 
    connecting **{optimal_route['Origin_Name']}** to **{optimal_route['Destination_Name']}**.
    
    - **Financial Impact:** Operational cost maintained at **${optimal_route['Base_Cost_USD']:,.2f}**.
    - **ESG Compliance:** Carbon emissions reduced/optimized to **{optimal_route['CO2_Emissions_Tons']} Tons**.
    - **
