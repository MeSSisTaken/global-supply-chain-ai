import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestRegressor
from sklearn.preprocessing import OneHotEncoder
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
import pulp

class DelayPredictor:
    """Makine Öğrenmesi Tabanlı Risk ve Gecikme Tahmin Motoru"""
    def __init__(self):
        self.categorical_features = ["Transport_Mode", "Weather_Condition", "Geopolitical_Risk"]
        self.numeric_features = ["Distance_KM", "Port_Congestion_Index"]
        
        preprocessor = ColumnTransformer(
            transformers=[
                ("num", "passthrough", self.numeric_features),
                ("cat", OneHotEncoder(handle_unknown="ignore"), self.categorical_features)
            ]
        )
        
        self.model = Pipeline(steps=[
            ("preprocessor", preprocessor),
            ("regressor", RandomForestRegressor(n_estimators=100, random_state=42))
        ])

    def train(self, df):
        X = df[self.numeric_features + self.categorical_features]
        y = df["Delay_Days"]
        self.model.fit(X, y)

    def predict_delay(self, sample_dict):
        df_sample = pd.DataFrame([sample_dict])
        return round(float(self.model.predict(df_sample)[0]), 1)


def optimize_supply_chain(df, cost_weight=0.4, time_weight=0.3, co2_weight=0.3):
    """
    Lineer Programlama (PuLP) ile Çok Amaçlı Rota Optimizasyonu:
    Minimize: (Ağırlıklı Maliyet) + (Ağırlıklı Zaman) + (Ağırlıklı CO2 Salınımı)
    """
    prob = pulp.LpProblem("Supply_Chain_Optimization", pulp.LpMinimize)
    
    # Karar Değişkenleri: Her rota seçeneği için ikili (0 veya 1) karar
    route_vars = pulp.LpVariable.dicts("Route", df.index, cat=pulp.LpBinary)
    
    # Değerleri 0 ile 1 arasında normalize etmek için maksimum değerler
    max_cost = df["Base_Cost_USD"].max()
    max_time = (df["Transit_Days"] + df["Delay_Days"]).max()
    max_co2 = df["CO2_Emissions_Tons"].max()
    
    # Amaç Fonksiyonu (Objective Function)
    prob += pulp.lpSum([
        route_vars[i] * (
            cost_weight * (df.loc[i, "Base_Cost_USD"] / max_cost) +
            time_weight * ((df.loc[i, "Transit_Days"] + df.loc[i, "Delay_Days"]) / max_time) +
            co2_weight * (df.loc[i, "CO2_Emissions_Tons"] / max_co2)
        )
        for i in df.index
    ])
    
    # Kısıt (Constraint): Tam olarak 1 optimal rota seçilmelidir
    prob += pulp.lpSum([route_vars[i] for i in df.index]) == 1
    
    # Problemi çöz
    prob.solve(pulp.PULP_CBC_CMD(msg=False))
    
    # Seçilen optimal rotanın indeksini bul
    selected_idx = None
    for i in df.index:
        if pulp.value(route_vars[i]) == 1:
            selected_idx = i
            break
            
    return df.loc[selected_idx]

if __name__ == "__main__":
    df = pd.read_csv("global_logistics_data.csv")
    
    # ML Tahmin Testi
    predictor = DelayPredictor()
    predictor.train(df)
    test_sample = {
        "Transport_Mode": "Sea Freight",
        "Weather_Condition": "Severe Typhoon",
        "Geopolitical_Risk": "High (Suez Crisis)",
        "Distance_KM": 12000,
        "Port_Congestion_Index": 8.5
    }
    predicted_delay = predictor.predict_delay(test_sample)
    print(f" [ML TEST] Yüksek Riskli Deniz Rotası İçin Tahmini Gecikme: {predicted_delay} Gün")
    
    # Optimizasyon Testi
    best_route = optimize_supply_chain(df, cost_weight=0.5, time_weight=0.2, co2_weight=0.3)
    print("\n [OPTIMIZER TEST] Seçilen En Optimal Rota:")
    print(f"   - Sevk ID: {best_route['Shipment_ID']}")
    print(f"   - Taşıma Modu: {best_route['Transport_Mode']}")
    print(f"   - Maliyet: ${best_route['Base_Cost_USD']:.2f}")
    print(f"   - CO2 Salınımı: {best_route['CO2_Emissions_Tons']} Ton")