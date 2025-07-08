import streamlit as st
import requests
import folium
import re
import time
from streamlit_folium import st_folium
from geopy.distance import geodesic

# Set Streamlit page config
st.set_page_config(page_title="⛽ Fuel Finder", layout="wide")
st.title("⛽ Fuel Station Finder in Pakistan")

# --- 🛢️ Enhanced Brand Logos ---
brand_icons = {
    "shell": "https://uxwing.com/wp-content/themes/uxwing/download/brands-shell/shell-icon.png",
    "pso": "https://static.cdnlogo.com/logos/p/9/pakistan-state-oil.svg",
    "total": "https://upload.wikimedia.org/wikipedia/commons/8/86/TotalEnergies_Logo.svg",
    "attock": "https://upload.wikimedia.org/wikipedia/en/thumb/3/35/Attock_Petroleum_Limited_logo.png/300px-Attock_Petroleum_Limited_logo.png",
    "hascol": "https://hascol.com/images/Hascol-Logo.png",
    "caltex": "https://upload.wikimedia.org/wikipedia/commons/4/4a/Caltex_logo.svg",
    "byco": "https://byco.com.pk/wp-content/uploads/2019/01/byco-logo.png",
    "go": "https://logos-world.net/wp-content/uploads/2021/02/GO-Logo.png"
}
# Default icon for unknown brands
DEFAULT_ICON = folium.Icon(color="green", icon="glyphicon glyphicon-tint")

# --- 📍 Comprehensive Pakistani Cities and Coordinates ---
cities = {
    # Major Cities
    "Lahore": (31.5204, 74.3587),
    "Karachi": (24.8607, 67.0011),
    "Islamabad": (33.6844, 73.0479),
    "Rawalpindi": (33.5651, 73.0169),
    "Faisalabad": (31.4504, 73.1350),
    "Peshawar": (34.0151, 71.5249),
    "Quetta": (30.1798, 66.9750),
    "Multan": (30.1575, 71.5249),
    "Hyderabad": (25.3960, 68.3578),
    "Sialkot": (32.4945, 74.5229),
    
    # Additional Important Cities
    "Gujranwala": (32.1877, 74.1945),
    "Sargodha": (32.0836, 72.6711),
    "Bahawalpur": (29.4000, 71.6833),
    "Sukkur": (27.7036, 68.8480),
    "Larkana": (27.5590, 68.2123),
    "Sheikhupura": (31.7167, 73.9667),
    "Jhang": (31.2681, 72.3317),
    "Gujrat": (32.5740, 74.0776),
    "Kasur": (31.1177, 74.4500),
    "Rahim Yar Khan": (28.4202, 70.2952),
    "Sahiwal": (30.6682, 73.1114),
    "Okara": (30.8081, 73.4444),
    "Wah Cantonment": (33.7948, 72.7348),
    "Dera Ghazi Khan": (30.0561, 70.6403),
    "Mirpur Khas": (25.5273, 69.0139),
    "Chiniot": (31.7200, 72.9800),
    "Kamoke": (31.9744, 74.2247),
    "Mandi Bahauddin": (32.5861, 73.4917),
    "Jhelum": (32.9425, 73.7257),
    "Sadiqabad": (28.3089, 70.1286),
    "Jacobabad": (28.2820, 68.4375),
    "Shikarpur": (27.9556, 68.6389),
    "Khanewal": (30.3017, 71.9319),
    "Hafizabad": (32.0669, 73.6881),
    "Kohat": (33.5919, 71.4392),
    "Mardan": (34.1983, 72.0406),
    "Mingora": (34.7797, 72.3608),
    "Nawabshah": (26.2442, 68.4100),
    "Abbottabad": (34.1463, 73.2119),
    "Muzaffargarh": (30.0769, 71.1928),
    "Muridke": (31.8000, 74.2667),
    "Pakpattan": (30.3436, 73.3831),
    "Tando Allahyar": (25.4667, 68.7167),
    "Jaranwala": (31.3333, 73.4167),
    "Chishtian": (29.7969, 72.8644),
    "Daska": (32.3269, 74.3506),
    "Mianwali": (32.5831, 71.5439),
    "Attock": (33.7669, 72.3700),
    "Vehari": (30.0453, 72.3489),
    "Ferozewala": (31.7831, 74.0731)
}

# --- 📌 User Input ---
st.sidebar.header("📍 Select Location & Parameters")
selected_city = st.sidebar.selectbox("Select City", list(cities.keys()))
latitude, longitude = cities[selected_city]

# Custom location option
st.sidebar.markdown("### 📍 Custom Location (Optional)")
use_custom = st.sidebar.checkbox("Use custom coordinates")
if use_custom:
    custom_lat = st.sidebar.number_input("Latitude", value=latitude, format="%.6f")
    custom_lon = st.sidebar.number_input("Longitude", value=longitude, format="%.6f")
    latitude, longitude = custom_lat, custom_lon

radius_km = st.sidebar.slider("Search Radius (km)", 1, 50, 10)

# --- 🌗 Theme Toggle ---
st.sidebar.markdown("### 🎨 Theme")
theme = st.sidebar.radio("Select Theme", ["Light", "Dark"], index=0)

# Set map tile based on theme
if theme == "Dark":
    map_tile = 'CartoDB Dark_Matter'
    st.markdown(
        """
        <style>
        body, .stApp, .css-1d391kg, .css-18e3th9, .css-1v0mbdj, .css-1cpxqw2, .css-ffhzg2, .css-1q8dd3e, .css-1d3w5wq, .css-1v4eu6x, .css-1b0udgb, .css-1v3fvcr, .css-1lcbmhc, .css-1r6slb0, .css-1vzeuhh, .css-1v0mbdj, .css-1cpxqw2, .css-1q8dd3e, .css-1d3w5wq, .css-1v4eu6x, .css-1b0udgb, .css-1v3fvcr, .css-1lcbmhc, .css-1r6slb0, .css-1vzeuhh {
            background-color: #18191A !important;
            color: #F5F6F7 !important;
        }
        .sidebar .sidebar-content, .css-1d391kg, .css-1v0mbdj, .css-1cpxqw2, .css-ffhzg2, .css-1q8dd3e, .css-1d3w5wq, .css-1v4eu6x, .css-1b0udgb, .css-1v3fvcr, .css-1lcbmhc, .css-1r6slb0, .css-1vzeuhh {
            background-color: #242526 !important;
            color: #F5F6F7 !important;
        }
        h1, h2, h3, h4, h5, h6, .stMarkdown, .stText, .stSubheader, .stHeader, .stTitle, .stSidebar, .stSidebarContent {
            color: #F5F6F7 !important;
        }
        </style>
        """,
        unsafe_allow_html=True
    )
else:
    map_tile = 'CartoDB Positron'
    st.markdown(
        """
        <style>
        body, .stApp, .css-1d391kg, .css-18e3th9, .css-1v0mbdj, .css-1cpxqw2, .css-ffhzg2, .css-1q8dd3e, .css-1d3w5wq, .css-1v4eu6x, .css-1b0udgb, .css-1v3fvcr, .css-1lcbmhc, .css-1r6slb0, .css-1vzeuhh {
            background-color: #FFFFFF !important;
            color: #262730 !important;
        }
        .sidebar .sidebar-content, .css-1d391kg, .css-1v0mbdj, .css-1cpxqw2, .css-ffhzg2, .css-1q8dd3e, .css-1d3w5wq, .css-1v4eu6x, .css-1b0udgb, .css-1v3fvcr, .css-1lcbmhc, .css-1r6slb0, .css-1vzeuhh {
            background-color: #F0F2F6 !important;
            color: #262730 !important;
        }
        h1, h2, h3, h4, h5, h6, .stMarkdown, .stText, .stSubheader, .stHeader, .stTitle, .stSidebar, .stSidebarContent {
            color: #262730 !important;
        }
        </style>
        """,
        unsafe_allow_html=True
    )

# --- Helper Functions ---
def is_english(text):
    """Check if text contains primarily English characters"""
    if not text:
        return False
    # Allow English letters, numbers, spaces, and common punctuation
    return bool(re.match(r'^[\x00-\x7F\s.,()\-\'"0-9A-Za-z/&]+$', text))

def clean_text(text):
    """Clean and normalize text"""
    if not text:
        return ""
    # Remove extra whitespace and normalize
    return re.sub(r'\s+', ' ', text.strip())

def extract_brand_from_name(name):
    """Extract brand from station name with better accuracy"""
    if not name:
        return "Unknown"
    
    name_lower = name.lower()
    
    # Pakistani fuel brands with common variations
    brand_patterns = {
        "Shell": ["shell"],
        "PSO": ["pso", "pakistan state oil", "pakistan state"],
        "Total": ["total", "total parco"],
        "Attock": ["attock", "apl"],
        "Hascol": ["hascol"],
        "Caltex": ["caltex"],
        "Byco": ["byco"],
        "GO": ["go petrol", "go fuel", " go "],
        "Hi-Octane": ["hi-octane", "hi octane", "hioctane"],
        "Petro Plus": ["petro plus", "petroplus"],
        "Speed": ["speed petrol", "speed fuel"],
        "Zoom": ["zoom petrol", "zoom fuel"]
    }
    
    # Check for exact brand matches
    for brand, patterns in brand_patterns.items():
        if any(pattern in name_lower for pattern in patterns):
            return brand
    
    # Check if it's a generic petrol pump
    generic_terms = ["petrol pump", "fuel station", "gas station", "filling station"]
    if any(term in name_lower for term in generic_terms):
        return "Generic Petrol Pump"
    
    return "Unknown"

def calculate_distance(lat1, lon1, lat2, lon2):
    """Calculate distance between two points using geopy"""
    try:
        distance = geodesic((lat1, lon1), (lat2, lon2)).kilometers
        return round(distance, 2)
    except:
        return None

def get_overpass_data(latitude, longitude, radius_km, max_retries=3):
    """Fetch fuel station data from Overpass API with retry logic"""
    
    # Convert radius from km to degrees (approximate)
    radius_deg = radius_km / 111.0
    south = latitude - radius_deg
    north = latitude + radius_deg
    west = longitude - radius_deg
    east = longitude + radius_deg
    
    # Enhanced Overpass query to get more fuel stations
    overpass_url = "https://overpass-api.de/api/interpreter"
    query = f"""
    [out:json][timeout:30];
    (
      node["amenity"="fuel"]({south},{west},{north},{east});
      node["amenity"="gas_station"]({south},{west},{north},{east});
      node["amenity"="petrol_station"]({south},{west},{north},{east});
      way["amenity"="fuel"]({south},{west},{north},{east});
      way["amenity"="gas_station"]({south},{west},{north},{east});
      way["amenity"="petrol_station"]({south},{west},{north},{east});
    );
    out center;
    """
    
    for attempt in range(max_retries):
        try:
            response = requests.get(overpass_url, params={"data": query}, timeout=30)
            response.raise_for_status()
            data = response.json()
            return data.get("elements", [])
        except requests.exceptions.RequestException as e:
            if attempt < max_retries - 1:
                st.warning(f"Attempt {attempt + 1} failed, retrying... ({e})")
                time.sleep(2)
            else:
                st.error(f"Failed to fetch data after {max_retries} attempts: {e}")
                return []
        except Exception as e:
            st.error(f"Unexpected error: {e}")
            return []

# --- 🔄 Fetch Data ---
st.info(f"🔍 Searching fuel stations near **{selected_city}** within {radius_km} km...")

with st.spinner("Fetching fuel station data..."):
    raw_fuel_stations = get_overpass_data(latitude, longitude, radius_km)

if not raw_fuel_stations:
    st.error("❌ No fuel stations found or API error occurred.")
    st.stop()

# --- Process and Clean Data ---
fuel_stations = []
processed_locations = set()  # To avoid duplicates

for station in raw_fuel_stations:
    # Handle both nodes and ways
    if station.get("type") == "way":
        if "center" in station:
            lat = station["center"]["lat"]
            lon = station["center"]["lon"]
        else:
            continue
    else:
        lat = station.get("lat")
        lon = station.get("lon")
    
    if not lat or not lon:
        continue
    
    # Check if within actual radius (more accurate than bounding box)
    distance = calculate_distance(latitude, longitude, lat, lon)
    if distance and distance > radius_km:
        continue
    
    # Avoid duplicates by checking location
    location_key = f"{lat:.6f},{lon:.6f}"
    if location_key in processed_locations:
        continue
    processed_locations.add(location_key)
    
    tags = station.get("tags", {})
    
    # Extract name with priority: name:en > name (if English) > brand > operator
    name = (
        tags.get("name:en") or
        (tags.get("name") if is_english(tags.get("name", "")) else None) or
        (tags.get("brand") if is_english(tags.get("brand", "")) else None) or
        (tags.get("operator") if is_english(tags.get("operator", "")) else None) or
        "Unnamed Station"
    )
    
    # Extract brand with priority: brand:en > brand (if English) > extract from name
    brand = (
        tags.get("brand:en") or
        (tags.get("brand") if is_english(tags.get("brand", "")) else None) or
        extract_brand_from_name(name)
    )
    
    # Extract address with multiple fallbacks
    address = (
        tags.get("addr:full:en") or
        tags.get("addr:street:en") or
        (tags.get("addr:full") if is_english(tags.get("addr:full", "")) else None) or
        (tags.get("addr:street") if is_english(tags.get("addr:street", "")) else None) or
        tags.get("addr:city") or
        "Address not available"
    )
    
    # Additional information
    phone = tags.get("phone", "N/A")
    website = tags.get("website", "N/A")
    opening_hours = tags.get("opening_hours", "N/A")
    fuel_types = []
    
    # Check for fuel types
    if tags.get("fuel:diesel") == "yes":
        fuel_types.append("Diesel")
    if tags.get("fuel:octane_91") == "yes":
        fuel_types.append("Octane 91")
    if tags.get("fuel:octane_95") == "yes":
        fuel_types.append("Octane 95")
    if tags.get("fuel:octane_97") == "yes":
        fuel_types.append("Octane 97")
    if tags.get("fuel:lpg") == "yes":
        fuel_types.append("LPG")
    if tags.get("fuel:cng") == "yes":
        fuel_types.append("CNG")
    
    # Only include if name and brand are in English
    if is_english(name) and is_english(brand):
        fuel_stations.append({
            "name": clean_text(name),
            "brand": clean_text(brand),
            "address": clean_text(address),
            "lat": lat,
            "lon": lon,
            "distance": distance,
            "phone": phone,
            "website": website,
            "opening_hours": opening_hours,
            "fuel_types": fuel_types
        })

# Sort by distance
fuel_stations.sort(key=lambda x: x["distance"] if x["distance"] else float('inf'))

st.success(f"✅ Found {len(fuel_stations)} fuel stations within {radius_km} km of {selected_city}.")

# --- Extract Available Brands ---
available_brands = set()
for station in fuel_stations:
    brand = station.get("brand", "Unknown")
    if brand and brand != "Unknown":
        available_brands.add(brand.strip())
available_brands = sorted(list(available_brands), key=lambda x: x.lower())

# --- Filters ---
st.sidebar.markdown("### 🔍 Filters")
selected_brand = st.sidebar.selectbox("Filter by Brand", ["All"] + available_brands)

# Distance filter - Fixed: Convert all values to float
max_distance = st.sidebar.slider("Maximum Distance (km)", 0.5, float(radius_km), float(radius_km), 0.5)

# --- 🗺️ Create Map ---
m = folium.Map(location=[latitude, longitude], zoom_start=12, tiles=None)
folium.TileLayer(map_tile, name=f'{theme} Tiles', control=False).add_to(m)

# Draw radius circle
folium.Circle(
    radius=radius_km * 1000,
    location=[latitude, longitude],
    color="blue",
    fill=True,
    fill_opacity=0.1,
    popup=f"Search Area: {radius_km} km radius"
).add_to(m)

# Add center marker
folium.Marker(
    [latitude, longitude],
    popup=f"Search Center: {selected_city}",
    icon=folium.Icon(color="red", icon="star")
).add_to(m)

# --- 📍 Filter and Display Stations ---
filtered_stations = []

for station in fuel_stations:
    # Apply filters
    if selected_brand != "All" and station["brand"] != selected_brand:
        continue
    
    if station["distance"] and station["distance"] > max_distance:
        continue
    
    filtered_stations.append(station)
    
    # Custom icon based on brand
    brand_key = station["brand"].lower()
    if brand_key in brand_icons:
        icon = folium.CustomIcon(brand_icons[brand_key], icon_size=(30, 30))
    else:
        icon = DEFAULT_ICON
    
    # Create enhanced popup
    fuel_info = ", ".join(station["fuel_types"]) if station["fuel_types"] else "Not specified"
    
    popup_html = f"""
    <div style="width: 250px;">
        <h4>{station['name']}</h4>
        <p><strong>Brand:</strong> {station['brand']}</p>
        <p><strong>Distance:</strong> {station['distance']} km</p>
        <p><strong>Address:</strong> {station['address']}</p>
        <p><strong>Fuel Types:</strong> {fuel_info}</p>
        <p><strong>Phone:</strong> {station['phone']}</p>
        <p><strong>Hours:</strong> {station['opening_hours']}</p>
    </div>
    """
    
    folium.Marker(
        [station["lat"], station["lon"]],
        popup=folium.Popup(popup_html, max_width=300),
        icon=icon
    ).add_to(m)

# Show map
st_folium(m, width=1200, height=600)

# --- Show Station Details ---
if filtered_stations:
    st.subheader(f"📋 Fuel Station Details ({len(filtered_stations)} stations)")
    
    # Display options
    col1, col2 = st.columns([2, 1])
    with col1:
        display_mode = st.radio("Display Mode", ["Compact", "Detailed"], horizontal=True)
    with col2:
        sort_by = st.selectbox("Sort by", ["Distance", "Name", "Brand"])
    
    # Sort stations
    if sort_by == "Distance":
        filtered_stations.sort(key=lambda x: x["distance"] if x["distance"] else float('inf'))
    elif sort_by == "Name":
        filtered_stations.sort(key=lambda x: x["name"].lower())
    elif sort_by == "Brand":
        filtered_stations.sort(key=lambda x: x["brand"].lower())
    
    # Display stations
    for i, station in enumerate(filtered_stations, 1):
        if display_mode == "Compact":
            st.markdown(f"""
            **{i}. {station['name']}** ({station['brand']})  
            📍 {station['address']} • 📏 {station['distance']} km
            """)
        else:
            col1, col2 = st.columns([3, 1])
            with col1:
                fuel_types_str = ", ".join(station["fuel_types"]) if station["fuel_types"] else "Not specified"
                st.markdown(f"""
                **{i}. {station['name']}**  
                🏢 Brand: {station['brand']}  
                📍 Address: {station['address']}  
                📏 Distance: {station['distance']} km  
                ⛽ Fuel Types: {fuel_types_str}  
                📞 Phone: {station['phone']}  
                🕒 Hours: {station['opening_hours']}
                """)
                if station['website'] != 'N/A':
                    st.markdown(f"🌐 Website: {station['website']}")
            
            with col2:
                maps_url = f"https://www.google.com/maps/dir/?api=1&destination={station['lat']},{station['lon']}"
                st.markdown(f"[📍 Directions]({maps_url})")
            
            st.divider()
else:
    st.warning("No fuel stations match your current filters.")

# --- Statistics ---
if fuel_stations:
    st.sidebar.markdown("### 📊 Statistics")
    total_stations = len(fuel_stations)
    filtered_count = len(filtered_stations)
    
    st.sidebar.metric("Total Found", total_stations)
    st.sidebar.metric("After Filters", filtered_count)
    
    # Brand distribution
    brand_counts = {}
    for station in fuel_stations:
        brand = station["brand"]
        brand_counts[brand] = brand_counts.get(brand, 0) + 1
    
    st.sidebar.markdown("**Brand Distribution:**")
    for brand, count in sorted(brand_counts.items(), key=lambda x: x[1], reverse=True)[:5]:
        st.sidebar.text(f"{brand}: {count}")