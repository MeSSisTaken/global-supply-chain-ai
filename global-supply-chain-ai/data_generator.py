import pandas as pd
import numpy as np

def generate_global_logistics_data(samples=500):
    np.random.seed(42)
    
    ports_origins = [
        {"name": "Shanghai Port", "lat": 31.2304, "lon": 121.4737},
        {"name": "Shenzhen Port", "lat": 22.5431, "lon": 114.0579},
        {"name": "Singapore Port", "lat": 1.3521, "lon": 103.8198},
        {"name": "Ambarli Port (Istanbul)", "lat": 40.9681, "lon": 28.6946}
    ]
    
    hubs_destinations = [
        {"name": "Rotterdam Hub", "lat": 51.9244, "lon": 4.4777},
        {"name": "Hamburg Hub", "lat": 53.5511, "lon": 9.9937},
        {"name": "Frankfurt Logistics Hub", "lat": 50.1109, "lon": 8.6821},
        {"name": "Port of Los Angeles", "lat": 33.7423, "lon": -118.2705}
    ]
    
    modes = ["Sea Freight", "Air Freight", "Rail Freight", "Road Freight"]
    weather_states = ["Clear", "Minor Storm", "Severe Typhoon", "Heavy Snow"]
    geopolitical_risks = ["Low", "Medium", "High (Suez Crisis)", "Extreme (Chokepoint Blocked)"]
    
    data = []
    
    for i in range(1, samples + 1):
        origin = np.random.choice(ports_origins)
        dest = np.random.choice(hubs_destinations)
        mode = np.random.choice(modes)
        weather = np.random.choice(weather_states, p=[0.6, 0.25, 0.1, 0.05])
        geo_risk = np.random.choice(geopolitical_risks, p=[0.7, 0.18, 0.09, 0.03])
        
        # Temel mesafeler ve katsayılar
        distance_km = np.random.uniform(2000, 18000)
        
        if mode == "Air Freight":
            base_cost = distance_km * np.random.uniform(4.5, 6.0)
            transit_days = distance_km / 8000 + np.random.uniform(1, 3)
            co2_emissions_tons = (distance_km * 0.0005) * np.random.uniform(1.8, 2.2)
        elif mode == "Sea Freight":
            base_cost = distance_km * np.random.uniform(0.8, 1.5)
            transit_days = distance_km / 800 + np.random.uniform(10, 25)
            co2_emissions_tons = (distance_km * 0.00005) * np.random.uniform(0.9, 1.1)
        elif mode == "Rail Freight":
            base_cost = distance_km * np.random.uniform(2.0, 3.2)
            transit_days = distance_km / 1500 + np.random.uniform(5, 10)
            co2_emissions_tons = (distance_km * 0.0001) * np.random.uniform(1.0, 1.3)
        else: # Road
            base_cost = distance_km * np.random.uniform(2.5, 3.8)
            transit_days = distance_km / 1200 + np.random.uniform(2, 6)
            co2_emissions_tons = (distance_km * 0.00015) * np.random.uniform(1.1, 1.4)

        # Risk çarpanları
        delay = 0
        if weather in ["Severe Typhoon", "Heavy Snow"]:
            delay += np.random.uniform(4, 12)
        if "High" in geo_risk or "Extreme" in geo_risk:
            delay += np.random.uniform(10, 20)
            base_cost *= 1.35
            
        data.append({
            "Shipment_ID": f"GLOBAL-EXP-{10000+i}",
            "Origin_Name": origin["name"],
            "Origin_Lat": origin["lat"],
            "Origin_Lon": origin["lon"],
            "Destination_Name": dest["name"],
            "Destination_Lat": dest["lat"],
            "Destination_Lon": dest["lon"],
            "Transport_Mode": mode,
            "Distance_KM": round(distance_km, 2),
            "Base_Cost_USD": round(base_cost, 2),
            "Transit_Days": round(transit_days, 1),
            "Delay_Days": round(delay, 1),
            "CO2_Emissions_Tons": round(co2_emissions_tons, 2),
            "Weather_Condition": weather,
            "Geopolitical_Risk": geo_risk,
            "Port_Congestion_Index": round(np.random.uniform(1.0, 10.0), 1)
        })
        
    df = pd.DataFrame(data)
    df.to_csv("global_logistics_data.csv", index=False)
    print(" [SUCCESS] 500 Global Multi-Modal Route Records generated: 'global_logistics_data.csv'")

if __name__ == "__main__":
    generate_global_logistics_data()