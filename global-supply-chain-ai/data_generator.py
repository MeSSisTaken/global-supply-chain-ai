import pandas as pd
import numpy as np
import math

# 200 Adet Küresel Lojistik Merkezi ve Koordinat Veritabanı
HUBS = [
    # Avrupa (50 Hub)
    {"name": "Istanbul, TR", "lat": 41.0082, "lon": 28.9784, "region": "Europe"},
    {"name": "Izmir, TR", "lat": 38.4237, "lon": 27.1428, "region": "Europe"},
    {"name": "Mersin, TR", "lat": 36.8121, "lon": 34.6415, "region": "Europe"},
    {"name": "Rotterdam, NL", "lat": 51.9244, "lon": 4.4777, "region": "Europe"},
    {"name": "Hamburg, DE", "lat": 53.5511, "lon": 9.9937, "region": "Europe"},
    {"name": "Antwerp, BE", "lat": 51.2194, "lon": 4.4025, "region": "Europe"},
    {"name": "London, UK", "lat": 51.5074, "lon": -0.1278, "region": "Europe"},
    {"name": "Felixstowe, UK", "lat": 51.9617, "lon": 1.3513, "region": "Europe"},
    {"name": "Le Havre, FR", "lat": 49.4944, "lon": 0.1079, "region": "Europe"},
    {"name": "Marseille, FR", "lat": 43.2965, "lon": 5.3698, "region": "Europe"},
    {"name": "Valencia, ES", "lat": 39.4699, "lon": -0.3763, "region": "Europe"},
    {"name": "Barcelona, ES", "lat": 41.3851, "lon": 2.1734, "region": "Europe"},
    {"name": "Algeciras, ES", "lat": 36.1408, "lon": -5.4562, "region": "Europe"},
    {"name": "Genoa, IT", "lat": 44.4056, "lon": 8.9463, "region": "Europe"},
    {"name": "Trieste, IT", "lat": 45.6495, "lon": 13.7768, "region": "Europe"},
    {"name": "Piraeus, GR", "lat": 37.9475, "lon": 23.6425, "region": "Europe"},
    {"name": "Gdansk, PL", "lat": 54.3520, "lon": 18.6466, "region": "Europe"},
    {"name": "Gothenburg, SE", "lat": 57.7089, "lon": 11.9746, "region": "Europe"},
    {"name": "Aarhus, DK", "lat": 56.1629, "lon": 10.2039, "region": "Europe"},
    {"name": "Koper, SI", "lat": 45.5481, "lon": 13.7302, "region": "Europe"},
    {"name": "Constanta, RO", "lat": 44.1792, "lon": 28.6498, "region": "Europe"},
    {"name": "Varna, BG", "lat": 43.2141, "lon": 27.9147, "region": "Europe"},
    {"name": "Berlin, DE", "lat": 52.5200, "lon": 13.4050, "region": "Europe"},
    {"name": "Munich, DE", "lat": 48.1351, "lon": 11.5820, "region": "Europe"},
    {"name": "Frankfurt, DE", "lat": 50.1109, "lon": 8.6821, "region": "Europe"},
    {"name": "Vienna, AT", "lat": 48.2082, "lon": 16.3738, "region": "Europe"},
    {"name": "Warsaw, PL", "lat": 52.2297, "lon": 21.0122, "region": "Europe"},
    {"name": "Prague, CZ", "lat": 50.0755, "lon": 14.4378, "region": "Europe"},
    {"name": "Budapest, HU", "lat": 47.4979, "lon": 19.0402, "region": "Europe"},
    {"name": "Madrid, ES", "lat": 40.4168, "lon": -3.7038, "region": "Europe"},
    {"name": "Lisbon, PT", "lat": 38.7223, "lon": -9.1393, "region": "Europe"},
    {"name": "Sines, PT", "lat": 37.9562, "lon": -8.8698, "region": "Europe"},
    {"name": "Dublin, IE", "lat": 53.3498, "lon": -6.2603, "region": "Europe"},
    {"name": "Copenhagen, DK", "lat": 55.6761, "lon": 12.5683, "region": "Europe"},
    {"name": "Oslo, NO", "lat": 59.9139, "lon": 10.7522, "region": "Europe"},
    {"name": "Helsinki, FI", "lat": 60.1699, "lon": 24.9384, "region": "Europe"},
    {"name": "Stockholm, SE", "lat": 59.3293, "lon": 18.0686, "region": "Europe"},
    {"name": "Tallinn, EE", "lat": 59.4370, "lon": 24.7536, "region": "Europe"},
    {"name": "Riga, LV", "lat": 56.9496, "lon": 24.1052, "region": "Europe"},
    {"name": "Klaipeda, LT", "lat": 55.7033, "lon": 21.1443, "region": "Europe"},
    {"name": "Zeebrugge, BE", "lat": 51.3308, "lon": 3.2064, "region": "Europe"},
    {"name": "Bremerhaven, DE", "lat": 53.5463, "lon": 8.5770, "region": "Europe"},
    {"name": "Wilhelmshaven, DE", "lat": 53.5186, "lon": 8.1317, "region": "Europe"},
    {"name": "Gioia Tauro, IT", "lat": 38.4286, "lon": 15.8986, "region": "Europe"},
    {"name": "Split, HR", "lat": 43.5081, "lon": 16.4402, "region": "Europe"},
    {"name": "Rijeka, HR", "lat": 45.3271, "lon": 14.4422, "region": "Europe"},
    {"name": "Thessaloniki, GR", "lat": 40.6401, "lon": 22.9444, "region": "Europe"},
    {"name": "Limassol, CY", "lat": 34.6786, "lon": 33.0413, "region": "Europe"},
    {"name": "Baku, AZ", "lat": 40.4093, "lon": 49.8671, "region": "Europe/Asia"},
    {"name": "Tbilisi, GE", "lat": 41.7151, "lon": 44.8271, "region": "Europe/Asia"},

    # Asya ve Pasifik (60 Hub)
    {"name": "Shanghai, CN", "lat": 31.2304, "lon": 121.4737, "region": "Asia"},
    {"name": "Ningbo, CN", "lat": 29.8683, "lon": 121.5440, "region": "Asia"},
    {"name": "Shenzhen, CN", "lat": 22.5431, "lon": 114.0579, "region": "Asia"},
    {"name": "Guangzhou, CN", "lat": 23.1291, "lon": 113.2644, "region": "Asia"},
    {"name": "Qingdao, CN", "lat": 36.0671, "lon": 120.3826, "region": "Asia"},
    {"name": "Tianjin, CN", "lat": 39.3434, "lon": 117.3616, "region": "Asia"},
    {"name": "Dalian, CN", "lat": 38.9140, "lon": 121.6147, "region": "Asia"},
    {"name": "Xiamen, CN", "lat": 24.4798, "lon": 118.0894, "region": "Asia"},
    {"name": "Hong Kong, HK", "lat": 22.3193, "lon": 114.1694, "region": "Asia"},
    {"name": "Busan, KR", "lat": 35.1796, "lon": 129.0756, "region": "Asia"},
    {"name": "Incheon, KR", "lat": 37.4563, "lon": 126.7052, "region": "Asia"},
    {"name": "Tokyo, JP", "lat": 35.6762, "lon": 139.6503, "region": "Asia"},
    {"name": "Yokohama, JP", "lat": 35.4437, "lon": 139.6380, "region": "Asia"},
    {"name": "Kobe, JP", "lat": 34.6901, "lon": 135.1955, "region": "Asia"},
    {"name": "Nagoya, JP", "lat": 35.1815, "lon": 136.9066, "region": "Asia"},
    {"name": "Osaka, JP", "lat": 34.6937, "lon": 135.5023, "region": "Asia"},
    {"name": "Singapore, SG", "lat": 1.3521, "lon": 103.8198, "region": "Asia"},
    {"name": "Port Klang, MY", "lat": 3.0000, "lon": 101.4000, "region": "Asia"},
    {"name": "Tanjung Pelepas, MY", "lat": 1.3631, "lon": 103.5486, "region": "Asia"},
    {"name": "Jakarta, ID", "lat": -6.2088, "lon": 106.8456, "region": "Asia"},
    {"name": "Surabaya, ID", "lat": -7.2575, "lon": 112.7521, "region": "Asia"},
    {"name": "Bangkok, TH", "lat": 13.7563, "lon": 100.5018, "region": "Asia"},
    {"name": "Laem Chabang, TH", "lat": 13.0800, "lon": 100.9100, "region": "Asia"},
    {"name": "Ho Chi Minh, VN", "lat": 10.8231, "lon": 106.6297, "region": "Asia"},
    {"name": "Haiphong, VN", "lat": 20.8449, "lon": 106.6881, "region": "Asia"},
    {"name": "Da Nang, VN", "lat": 16.0544, "lon": 108.2022, "region": "Asia"},
    {"name": "Manila, PH", "lat": 14.5995, "lon": 120.9842, "region": "Asia"},
    {"name": "Kaohsiung, TW", "lat": 22.6273, "lon": 120.3014, "region": "Asia"},
    {"name": "Taipei, TW", "lat": 25.0330, "lon": 121.5654, "region": "Asia"},
    {"name": "Mumbai, IN", "lat": 19.0760, "lon": 72.8777, "region": "Asia"},
    {"name": "Nhava Sheva, IN", "lat": 18.9500, "lon": 72.9500, "region": "Asia"},
    {"name": "Mundra, IN", "lat": 22.8389, "lon": 69.7217, "region": "Asia"},
    {"name": "Chennai, IN", "lat": 13.0827, "lon": 80.2707, "region": "Asia"},
    {"name": "Kolkata, IN", "lat": 22.5726, "lon": 88.3639, "region": "Asia"},
    {"name": "Cochin, IN", "lat": 9.9312, "lon": 76.2673, "region": "Asia"},
    {"name": "Colombo, LK", "lat": 6.9271, "lon": 79.8612, "region": "Asia"},
    {"name": "Chittagong, BD", "lat": 22.3569, "lon": 91.7832, "region": "Asia"},
    {"name": "Karachi, PK", "lat": 24.8607, "lon": 67.0011, "region": "Asia"},
    {"name": "Qasim, PK", "lat": 24.7700, "lon": 67.3300, "region": "Asia"},
    {"name": "Tashkent, UZ", "lat": 41.2995, "lon": 69.2401, "region": "Asia"},
    {"name": "Almaty, KZ", "lat": 43.2220, "lon": 76.8512, "region": "Asia"},
    {"name": "Astana, KZ", "lat": 51.1694, "lon": 71.4491, "region": "Asia"},
    {"name": "Bishkek, KG", "lat": 42.8746, "lon": 74.5698, "region": "Asia"},
    {"name": "Ulaanbaatar, MN", "lat": 47.8864, "lon": 106.9057, "region": "Asia"},
    {"name": "Sydney, AU", "lat": -33.8688, "lon": 151.2093, "region": "Oceania"},
    {"name": "Melbourne, AU", "lat": -37.8136, "lon": 144.9631, "region": "Oceania"},
    {"name": "Brisbane, AU", "lat": -27.4705, "lon": 153.0260, "region": "Oceania"},
    {"name": "Fremantle, AU", "lat": -32.0569, "lon": 115.7428, "region": "Oceania"},
    {"name": "Adelaide, AU", "lat": -34.9285, "lon": 138.6007, "region": "Oceania"},
    {"name": "Auckland, NZ", "lat": -36.8485, "lon": 174.7633, "region": "Oceania"},
    {"name": "Tauranga, NZ", "lat": -37.6878, "lon": 176.1651, "region": "Oceania"},
    {"name": "Wellington, NZ", "lat": -41.2865, "lon": 174.7762, "region": "Oceania"},
    {"name": "Port Moresby, PG", "lat": -9.4438, "lon": 147.1803, "region": "Oceania"},
    {"name": "Suva, FJ", "lat": -18.1416, "lon": 178.4419, "region": "Oceania"},
    {"name": "Yangon, MM", "lat": 16.8661, "lon": 96.1951, "region": "Asia"},
    {"name": "Phnom Penh, KH", "lat": 11.5564, "lon": 104.9282, "region": "Asia"},
    {"name": "Vientiane, LA", "lat": 17.9757, "lon": 102.6331, "region": "Asia"},
    {"name": "Bandar Seri Begawan, BN", "lat": 4.9031, "lon": 114.9398, "region": "Asia"},

    # Kuzey ve Güney Amerika (50 Hub)
    {"name": "New York, US", "lat": 40.7128, "lon": -74.0060, "region": "Americas"},
    {"name": "Los Angeles, US", "lat": 34.0522, "lon": -118.2437, "region": "Americas"},
    {"name": "Long Beach, US", "lat": 33.7701, "lon": -118.1937, "region": "Americas"},
    {"name": "Chicago, US", "lat": 41.8781, "lon": -87.6298, "region": "Americas"},
    {"name": "Houston, US", "lat": 29.7604, "lon": -95.3698, "region": "Americas"},
    {"name": "Savannah, US", "lat": 32.0809, "lon": -81.0912, "region": "Americas"},
    {"name": "Seattle, US", "lat": 47.6062, "lon": -122.3321, "region": "Americas"},
    {"name": "Oakland, US", "lat": 37.8044, "lon": -122.2712, "region": "Americas"},
    {"name": "Miami, US", "lat": 25.7617, "lon": -80.1918, "region": "Americas"},
    {"name": "Charleston, US", "lat": 32.7765, "lon": -79.9311, "region": "Americas"},
    {"name": "Norfolk, US", "lat": 36.8508, "lon": -76.2859, "region": "Americas"},
    {"name": "Vancouver, CA", "lat": 49.2827, "lon": -123.1207, "region": "Americas"},
    {"name": "Montreal, CA", "lat": 45.5017, "lon": -73.5673, "region": "Americas"},
    {"name": "Toronto, CA", "lat": 43.6532, "lon": -79.3832, "region": "Americas"},
    {"name": "Prince Rupert, CA", "lat": 54.3150, "lon": -130.3208, "region": "Americas"},
    {"name": "Halifax, CA", "lat": 44.6488, "lon": -63.5752, "region": "Americas"},
    {"name": "Manzanillo, MX", "lat": 19.0522, "lon": -104.3158, "region": "Americas"},
    {"name": "Lazaro Cardenas, MX", "lat": 17.9583, "lon": -102.2000, "region": "Americas"},
    {"name": "Veracruz, MX", "lat": 19.1738, "lon": -96.1342, "region": "Americas"},
    {"name": "Altamira, MX", "lat": 22.3931, "lon": -97.9378, "region": "Americas"},
    {"name": "Mexico City, MX", "lat": 19.4326, "lon": -99.1332, "region": "Americas"},
    {"name": "Panama City, PA", "lat": 8.9824, "lon": -79.5199, "region": "Americas"},
    {"name": "Colon, PA", "lat": 9.3598, "lon": -79.9014, "region": "Americas"},
    {"name": "Cartagena, CO", "lat": 10.3997, "lon": -75.5144, "region": "Americas"},
    {"name": "Buenaventura, CO", "lat": 3.8801, "lon": -77.0312, "region": "Americas"},
    {"name": "Bogota, CO", "lat": 4.7110, "lon": -74.0721, "region": "Americas"},
    {"name": "Callao, PE", "lat": -12.0565, "lon": -77.1181, "region": "Americas"},
    {"name": "Lima, PE", "lat": -12.0464, "lon": -77.0428, "region": "Americas"},
    {"name": "Valparaiso, CL", "lat": -33.0472, "lon": -71.6127, "region": "Americas"},
    {"name": "San Antonio, CL", "lat": -33.5947, "lon": -71.6075, "region": "Americas"},
    {"name": "Santiago, CL", "lat": -33.4489, "lon": -70.6693, "region": "Americas"},
    {"name": "Buenos Aires, AR", "lat": -34.6037, "lon": -58.3816, "region": "Americas"},
    {"name": "Santos, BR", "lat": -23.9608, "lon": -46.3339, "region": "Americas"},
    {"name": "Rio de Janeiro, BR", "lat": -22.9068, "lon": -43.1729, "region": "Americas"},
    {"name": "Paranagua, BR", "lat": -25.5200, "lon": -48.5090, "region": "Americas"},
    {"name": "Itajai, BR", "lat": -26.9078, "lon": -48.6619, "region": "Americas"},
    {"name": "Suape, BR", "lat": -8.3944, "lon": -34.9567, "region": "Americas"},
    {"name": "Montevideo, UY", "lat": -34.9011, "lon": -56.1645, "region": "Americas"},
    {"name": "Guayaquil, EC", "lat": -2.1894, "lon": -79.8891, "region": "Americas"},
    {"name": "Asuncion, PY", "lat": -25.2637, "lon": -57.5759, "region": "Americas"},
    {"name": "La Paz, BO", "lat": -16.4897, "lon": -68.1193, "region": "Americas"},
    {"name": "San Jose, CR", "lat": 9.9281, "lon": -84.0907, "region": "Americas"},
    {"name": "Kingston, JM", "lat": 17.9716, "lon": -76.7936, "region": "Americas"},
    {"name": "Freeport, BS", "lat": 26.5333, "lon": -78.7000, "region": "Americas"},
    {"name": "Caucedo, DO", "lat": 18.4200, "lon": -69.6300, "region": "Americas"},

    # Orta Doğu ve Afrika (40 Hub)
    {"name": "Jebel Ali (Dubai), AE", "lat": 24.9857, "lon": 55.0273, "region": "Middle East"},
    {"name": "Abu Dhabi, AE", "lat": 24.4539, "lon": 54.3773, "region": "Middle East"},
    {"name": "Jeddah, SA", "lat": 21.4858, "lon": 39.1925, "region": "Middle East"},
    {"name": "Dammam, SA", "lat": 26.4207, "lon": 50.0888, "region": "Middle East"},
    {"name": "King Abdullah Port, SA", "lat": 22.5100, "lon": 39.0800, "region": "Middle East"},
    {"name": "Salalah, OM", "lat": 17.0151, "lon": 54.0924, "region": "Middle East"},
    {"name": "Sohar, OM", "lat": 24.3461, "lon": 56.7075, "region": "Middle East"},
    {"name": "Doha, QA", "lat": 25.2854, "lon": 51.5310, "region": "Middle East"},
    {"name": "Manama, BH", "lat": 26.2285, "lon": 50.5860, "region": "Middle East"},
    {"name": "Kuwait City, KW", "lat": 29.3759, "lon": 47.9774, "region": "Middle East"},
    {"name": "Aqaba, JO", "lat": 29.5321, "lon": 35.0063, "region": "Middle East"},
    {"name": "Haifa, IL", "lat": 32.7940, "lon": 34.9896, "region": "Middle East"},
    {"name": "Ashdod, IL", "lat": 31.8044, "lon": 34.6553, "region": "Middle East"},
    {"name": "Beirut, LB", "lat": 33.8938, "lon": 35.5018, "region": "Middle East"},
    {"name": "Alexandria, EG", "lat": 31.2001, "lon": 29.9187, "region": "Africa"},
    {"name": "Port Said, EG", "lat": 31.2653, "lon": 32.3019, "region": "Africa"},
    {"name": "Damietta, EG", "lat": 31.4165, "lon": 31.8133, "region": "Africa"},
    {"name": "Tangier Med, MA", "lat": 35.8884, "lon": -5.5028, "region": "Africa"},
    {"name": "Casablanca, MA", "lat": 33.5731, "lon": -7.5898, "region": "Africa"},
    {"name": "Algiers, DZ", "lat": 36.7538, "lon": 3.0588, "region": "Africa"},
    {"name": "Tunis, TN", "lat": 36.8065, "lon": 10.1815, "region": "Africa"},
    {"name": "Tripoli, LY", "lat": 32.8872, "lon": 13.1913, "region": "Africa"},
    {"name": "Lagos (Apapa), NG", "lat": 6.4549, "lon": 3.3887, "region": "Africa"},
    {"name": "Tema, GH", "lat": 5.6698, "lon": -0.0166, "region": "Africa"},
    {"name": "Abidjan, CI", "lat": 5.3599, "lon": -4.0083, "region": "Africa"},
    {"name": "Dakar, SN", "lat": 14.7167, "lon": -17.4677, "region": "Africa"},
    {"name": "Durban, ZA", "lat": -29.8587, "lon": 31.0218, "region": "Africa"},
    {"name": "Cape Town, ZA", "lat": -33.9249, "lon": 18.4241, "region": "Africa"},
    {"name": "Coega (Port Elizabeth), ZA", "lat": -33.8058, "lon": 25.6747, "region": "Africa"},
    {"name": "Mombasa, KE", "lat": -4.0435, "lon": 39.6682, "region": "Africa"},
    {"name": "Dar es Salaam, TZ", "lat": -6.7924, "lon": 39.2083, "region": "Africa"},
    {"name": "Djibouti, DJ", "lat": 11.5721, "lon": 43.1456, "region": "Africa"},
    {"name": "Luanda, AO", "lat": -8.8390, "lon": 13.2894, "region": "Africa"},
    {"name": "Maputo, MZ", "lat": -25.9692, "lon": 32.5732, "region": "Africa"},
    {"name": "Port Louis, MU", "lat": -20.1609, "lon": 57.5012, "region": "Africa"},
    {"name": "Walvis Bay, NA", "lat": -22.9575, "lon": 14.5053, "region": "Africa"},
    {"name": "Douala, CM", "lat": 4.0511, "lon": 9.7679, "region": "Africa"},
    {"name": "Pointe-Noire, CG", "lat": -4.7692, "lon": 11.8664, "region": "Africa"},
    {"name": "Riyadh, SA", "lat": 24.7136, "lon": 46.6753, "region": "Middle East"},
    {"name": "Basra, IQ", "lat": 30.5081, "lon": 47.7835, "region": "Middle East"}
]

def haversine(lat1, lon1, lat2, lon2):
    """İki küresel koordinat arasındaki gerçek mesafeyi (KM) hesaplar."""
    R = 6371.0 # Dünya yarıçapı
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = math.sin(dlat / 2)**2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon / 2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return R * c

def generate_global_logistics_data():
    np.random.seed(42)
    transport_modes = ["Sea Freight", "Air Freight", "Rail Freight", "Road Freight"]
    weather_conditions = ["Clear", "Stormy", "Foggy", "Heavy Rain", "Snow"]
    geopolitical_risks = ["Low", "Medium", "High", "Critical"]

    rows = []
    shipment_counter = 1000

    # 200 hub arasında dinamik rotalar türet (Yaklaşık 1500 koridor)
    for i in range(len(HUBS)):
        # Her hub en az 7-8 farklı merkeze bağlansın
        dest_indices = np.random.choice([j for j in range(len(HUBS)) if j != i], size=8, replace=False)
        for d_idx in dest_indices:
            origin = HUBS[i]
            dest = HUBS[d_idx]
            
            dist_km = haversine(origin["lat"], origin["lon"], dest["lat"], dest["lon"])
            
            # Mesafe sınırına göre geçerli modları belirle
            valid_modes = ["Air Freight"]
            if dist_km < 12000:
                valid_modes.append("Sea Freight")
            if dist_km < 4000:
                valid_modes.append("Rail Freight")
            if dist_km < 2500:
                valid_modes.append("Road Freight")

            for mode in valid_modes:
                shipment_counter += 1
                
                # Taşıma moduna özel katsayılar
                if mode == "Air Freight":
                    cost_per_km = np.random.uniform(1.8, 2.5)
                    speed_kmh = 750
                    co2_per_km = 0.0006
                elif mode == "Sea Freight":
                    cost_per_km = np.random.uniform(0.15, 0.35)
                    speed_kmh = 35
                    co2_per_km = 0.00008
                elif mode == "Rail Freight":
                    cost_per_km = np.random.uniform(0.4, 0.7)
                    speed_kmh = 60
                    co2_per_km = 0.00018
                else: # Road Freight
                    cost_per_km = np.random.uniform(0.8, 1.2)
                    speed_kmh = 70
                    co2_per_km = 0.00035

                base_cost = round(dist_km * cost_per_km, 2)
                transit_days = round(dist_km / (speed_kmh * 24), 1)
                co2_emissions = round(dist_km * co2_per_km, 2)
                
                geo_risk = np.random.choice(geopolitical_risks, p=[0.5, 0.3, 0.15, 0.05])
                weather = np.random.choice(weather_conditions, p=[0.6, 0.15, 0.1, 0.1, 0.05])
                port_congestion = round(np.random.uniform(1.0, 10.0), 1)

                # ML Hedef Değişkeni: Gecikme Süresi (Gün)
                delay_days = 0
                if geo_risk == "Critical": delay_days += np.random.uniform(4, 9)
                elif geo_risk == "High": delay_days += np.random.uniform(2, 5)
                
                if weather in ["Stormy", "Snow"]: delay_days += np.random.uniform(1.5, 4)
                if port_congestion > 7.0: delay_days += np.random.uniform(1, 3)

                delay_days = round(delay_days, 1)

                rows.append({
                    "Shipment_ID": f"SHP-{shipment_counter}",
                    "Origin_Name": origin["name"],
                    "Origin_Lat": origin["lat"],
                    "Origin_Lon": origin["lon"],
                    "Destination_Name": dest["name"],
                    "Destination_Lat": dest["lat"],
                    "Destination_Lon": dest["lon"],
                    "Transport_Mode": mode,
                    "Distance_KM": round(dist_km, 1),
                    "Base_Cost_USD": base_cost,
                    "Transit_Days": transit_days if transit_days > 0.5 else 0.5,
                    "CO2_Emissions_Tons": co2_emissions,
                    "Geopolitical_Risk": geo_risk,
                    "Weather_Condition": weather,
                    "Port_Congestion_Index": port_congestion,
                    "Delay_Days": delay_days
                })

    df = pd.DataFrame(rows)
    return df

if __name__ == "__main__":
    df = generate_global_logistics_data()
    df.to_csv("global_logistics_data.csv", index=False)
    print(f"Başarıyla {len(df)} adet canlı rota verisi üretildi!")
