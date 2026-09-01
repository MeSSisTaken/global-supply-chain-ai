import os
import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from optimizer import DelayPredictor, optimize_supply_chain
from data_generator import generate_global_logistics_data

# Bulunulan klasörün tam yolunu alma
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_PATH = os.path.join(BASE_DIR, "global_logistics_data.csv")

# Streamlit Sayfa Düzenleme
st.set_page_config(
    page_title="Global Supply Chain Resilience Engine", 
    layout="wide", 
    page_icon="🌍"
)

# Başlık
st.title("🌍 Global Multi-Modal Supply Chain Resilience & ESG Engine")
st.markdown("**Enterprise AI Platform** | Real-Time Route Optimization, ML Delay Forecasting & Emissions Control")
st.divider()

# Veri Yükleme
@st.cache_data
def load_data():
    if os.path.exists(DATA_PATH):
        return pd.read_csv(DATA_PATH)
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

# --- SIDEBAR: C-LEVEL STRATEJİ KONTROLLERİ ---
st.sidebar.header("🎯 C-Level Strategy Controls")
st.sidebar.caption("Bu paneller şirketin önceliğine göre yapay zeka optimizasyon ağırlıklarını değiştirir.")

st.sidebar.subheader("1. Optimization Weights")
cost_weight = st.sidebar.slider("💰 Cost Priority (%)", 0.0, 1.0, 0.4, 0.05)
time_weight = st.sidebar.slider("⏱️ Transit & Delay Priority (%)", 0.0, 1.0, 0.3, 0.05)
co2_weight = st.sidebar.slider("🌱 CO2 Emission Priority (%)", 0.0, 1.0, 0.3, 0.05)

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
    # PuLP Optimizasyon Motoru
    optimal_route = optimize_supply_chain(filtered_df, cost_weight, time_weight, co2_weight)

    # --- ROTA DETAY KARTI (NEREDEN NEREYE & ZAMAN TAHMİNİ) ---
    st.subheader("📍 Active Optimal Corridor & Detailed ETA Breakdown")
    
    st.markdown(f"### 🚀 **{optimal_route['Origin_Name']}** ➡️ **{optimal_route['Destination_Name']}**")
    
    total_eta = round(optimal_route['Transit_Days'] + optimal_route['Delay_Days'], 1)
    
    m_col1, m_col2, m_col3, m_col4, m_col5 = st.columns(5)
    m_col1.metric("Selected Route ID", optimal_route["Shipment_ID"])
    m_col2.metric("Transport Mode", optimal_route["Transport_Mode"])
    m_col3.metric("Base Transit Time", f"{optimal_route['Transit_Days']} Days")
    m_col4.metric("AI Predicted Delay", f"+{optimal_route['Delay_Days']} Days")
    m_col5.metric("Total ETA (Arrival Time)", f"{total_eta} Days", delta=f"{optimal_route['Delay_Days']} Days Delay", delta_color="inverse")

    st.divider()

    # --- STRATEJİK SENARYO KARŞILAŞTIRMASI (C-LEVEL CONTROLS NEDEN ÖNEMLİ?) ---
    st.subheader("⚖️ Strategic Scenario Benchmark (C-Level Trade-off Analysis)")
    st.caption("Aşağıdaki tablo, sizin seçtiğiniz stratejik ağırlıklar ile alternatif stratejilerin karşılaştırmasını gösterir:")

    # Alternatif Senaryolar
    pure_cost_route = optimize_supply_chain(filtered_df, cost_weight=1.0, time_weight=0.0, co2_weight=0.0)
    pure_time_route = optimize_supply_chain(filtered_df, cost_weight=0.0, time_weight=1.0, co2_weight=0.0)
    pure_co2_route  = optimize_supply_chain(filtered_df, cost_weight=0.0, time_weight=0.0, co2_weight=1.0)

    comparison_data = [
        {
            "Strategy": "🎯 CEO Custom Strategy (Your Selection)",
            "Mode": optimal_route["Transport_Mode"],
            "Total Cost ($)": f"${optimal_route['Base_Cost_USD']:,.2f}",
            "Total ETA (Days)": f"{total_eta} Days",
            "CO2 Emissions": f"{optimal_route['CO2_Emissions_Tons']} Tons"
        },
        {
            "Strategy": "💵 Pure Cost Optimization (Lowest Price)",
            "Mode": pure_cost_route["Transport_Mode"],
            "Total Cost ($)": f"${pure_cost_route['Base_Cost_USD']:,.2f}",
            "Total ETA (Days)": f"{round(pure_cost_route['Transit_Days'] + pure_cost_route['Delay_Days'], 1)} Days",
            "CO2 Emissions": f"{pure_cost_route['CO2_Emissions_Tons']} Tons"
        },
        {
            "Strategy": "⚡ Fastest Delivery (Minimum Delay)",
            "Mode": pure_time_route["Transport_Mode"],
            "Total Cost ($)": f"${pure_time_route['Base_Cost_USD']:,.2f}",
            "Total ETA (Days)": f"{round(pure_time_route['Transit_Days'] + pure_time_route['Delay_Days'], 1)} Days",
            "CO2 Emissions": f"{pure_time_route['CO2_Emissions_Tons']} Tons"
        },
        {
            "Strategy": "🌱 Green / Low Emission (ESG Target)",
            "Mode": pure_co2_route["Transport_Mode"],
            "Total Cost ($)": f"${pure_co2_route['Base_Cost_USD']:,.2f}",
            "Total ETA (Days)": f"{round(pure_co2_route['Transit_Days'] + pure_co2_route['Delay_Days'], 1)} Days",
            "CO2 Emissions": f"{pure_co2_route['CO2_Emissions_Tons']} Tons"
        }
    ]
    st.table(pd.DataFrame(comparison_data))

    st.divider()

    # --- CANLI ROTA HARİTASI (ÇİZGİSEL VE MODA GÖRE STİL) ---
    col_left, col_right = st.columns([2, 1])

    with col_left:
        st.subheader("🌐 Interactive Global Route Trajectory Visualizer")
        
        fig = go.Figure()

        # Tüm Çıkış ve Varış Noktaları (Arka plan)
        fig.add_trace(go.Scattergeo(
            lon = filtered_df['Origin_Lon'].tolist() + filtered_df['Destination_Lon'].tolist(),
            lat = filtered_df['Origin_Lat'].tolist() + filtered_df['Destination_Lat'].tolist(),
            hovertext = filtered_df['Origin_Name'].tolist() + filtered_df['Destination_Name'].tolist(),
            mode = 'markers',
            marker = dict(size=8, color='gray', opacity=0.5),
            name = "Logistics Hubs"
        ))

        # Modlara Göre Çizgi Stilleri ve Renkler
        mode_styles = {
            "Air Freight": {"color": "#ef553b", "dash": "dash", "width": 2},
            "Sea Freight": {"color": "#00cc96", "dash": "solid", "width": 4},
            "Rail Freight": {"color": "#ab63fa", "dash": "dot", "width": 3},
            "Road Freight": {"color": "#ffa15a", "dash": "solid", "width": 3}
        }

        # Seçilen Optimal Rotayı Çiz
        opt_mode = optimal_route["Transport_Mode"]
        style = mode_styles.get(opt_mode, {"color": "red", "dash": "solid", "width": 3})

        fig.add_trace(go.Scattergeo(
            lon = [optimal_route["Origin_Lon"], optimal_route["Destination_Lon"]],
            lat = [optimal_route["Origin_Lat"], optimal_route["Destination_Lat"]],
            mode = 'lines+markers',
            line = dict(width=style["width"], color=style["color"], dash=style["dash"]),
            marker = dict(size=12, color=style["color"]),
            name = f"OPTIMAL: {optimal_route['Origin_Name']} ➡️ {optimal_route['Destination_Name']} ({opt_mode})"
        ))

        fig.update_layout(
            geo = dict(
                projection_type = 'natural earth',
                showland = True,
                landcolor = 'rgb(243, 243, 243)',
                countrycolor = 'rgb(204, 204, 204)'
            ),
            margin = dict(l=0, r=0, t=30, b=0),
            height = 450
        )
        st.plotly_chart(fig, use_container_width=True)

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

    # ML GECİKME TAHMİNCİSİ
    st.subheader("🤖 Real-Time ML Delay Predictor")
    st.caption("Operasyonel senaryolara göre Makine Öğrenmesi modelinin gecikme tahminini test edin:")
    
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

    # CEO YÖNETİCİ ÖZET RAPORU
    st.subheader("📝 Executive Briefing (Automated C-Level Summary)")
    
    c_pct = int(cost_weight * 100)
    t_pct = int(time_weight * 100)
    co2_pct = int(co2_weight * 100)
    ship_id = optimal_route['Shipment_ID']
    t_mode = optimal_route['Transport_Mode']
    o_name = optimal_route['Origin_Name']
    d_name = optimal_route['Destination_Name']
    cost_val = round(optimal_route['Base_Cost_USD'], 2)
    co2_val = optimal_route['CO2_Emissions_Tons']
    delay_val = optimal_route['Delay_Days']

    summary_text = (
        f"**Strategic AI Recommendation:**\n"
        f"Based on operational constraints (Cost Weight: **{c_pct}%**, Time Weight: **{t_pct}%**, CO2 Weight: **{co2_pct}%**), "
        f"the engine identifies **{ship_id}** via **{t_mode}** as the optimal resilient route connecting **{o_name}** to **{d_name}**.\n\n"
        f"- **Financial Impact:** Operational cost maintained at **${cost_val:,.2f}**.\n"
        f"- **ESG Compliance:** Carbon emissions reduced/optimized to **{co2_val} Tons**.\n"
        f"- **Disruption Strategy:** Rerouted away from high-risk corridors while absorbing a predicted delay of **{delay_val} days** (Total ETA: **{total_eta} Days**)."
    )
    st.success(summary_text)
