import streamlit as st
import requests
import folium
import re
from streamlit_folium import st_folium

# Set Streamlit page config
st.set_page_config(page_title="⛽ Fuel Finder", layout="wide")
st.title("⛽ Fuel Station Finder in Pakistan")

# --- 🛢️ Known Brand Logos ---
brand_icons = {
    "shell": "https://uxwing.com/wp-content/themes/uxwing/download/brands-shell/shell-icon.png",
    "pso": "https://static.cdnlogo.com/logos/p/9/pakistan-state-oil.svg",
    "total": "https://upload.wikimedia.org/wikipedia/commons/8/86/TotalEnergies_Logo.svg",
    "attock": "https://upload.wikimedia.org/wikipedia/en/thumb/3/35/Attock_Petroleum_Limited_logo.png/300px-Attock_Petroleum_Limited_logo.png",
    "hascol": "https://hascol.com/images/Hascol-Logo.png"
}
# Default icon for unknown brands
DEFAULT_ICON = folium.Icon(color="green", icon="glyphicon glyphicon-tint")

# --- 📍 Main Pakistani Cities and Coordinates ---
cities = {
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
}

# --- 📌 User Input ---
st.sidebar.header("📍 Select City & Radius")
selected_city = st.sidebar.selectbox("Select City", list(cities.keys()))
latitude, longitude = cities[selected_city]
radius_km = st.sidebar.slider("Radius (km)", 1, 20, 5)

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

# Convert radius from km to degrees (~1 deg ≈ 111 km)
radius_deg = radius_km / 111
south = latitude - radius_deg
north = latitude + radius_deg
west = longitude - radius_deg
east = longitude + radius_deg

# --- 🔍 Overpass API Query ---
overpass_url = "https://overpass-api.de/api/interpreter"
query = f"""
[out:json];
node
  [amenity=fuel]
  ({south},{west},{north},{east});
out;
"""

# --- Helper: Check if text is English ---
def is_english(text):
    return bool(re.match(r'^[\x00-\x7F\s.,()\-\'"0-9A-Za-z]+$', text))

# --- 🔄 Fetch Data ---
st.info(f"🔍 Searching fuel stations near **{selected_city}**...")
try:
    response = requests.get(overpass_url, params={"data": query})
    data = response.json()
    fuel_stations = data.get("elements", [])
    st.success(f"✅ Found {len(fuel_stations)} fuel stations within {radius_km} km of {selected_city}.")
except Exception as e:
    st.error(f"❌ Failed to fetch data: {e}")
    fuel_stations = []

# --- Extract Available Brands ---
available_brands = set()
for station in fuel_stations:
    tags = station.get("tags", {})
    brand = tags.get("brand:en") or (tags.get("brand") if is_english(tags.get("brand", "")) else None)
    if brand:
        available_brands.add(brand.strip())
available_brands = sorted(list(available_brands), key=lambda x: x.lower())

# --- Brand Filter Dropdown ---
st.sidebar.markdown("### 🔍 Filter by Brand")
selected_brand = st.sidebar.selectbox("Select Brand (optional)", ["All"] + available_brands)

# --- 🗺️ Create Map ---
m = folium.Map(location=[latitude, longitude], zoom_start=13, tiles=None)
folium.TileLayer(map_tile, name=f'{theme} Tiles', control=False).add_to(m)

# Draw radius circle
folium.Circle(
    radius=radius_km * 1000,
    location=[latitude, longitude],
    color="blue",
    fill=True,
    fill_opacity=0.1
).add_to(m)

# --- 📍 Filter + Display Stations ---
filtered_stations = []

for station in fuel_stations:
    lat = station["lat"]
    lon = station["lon"]
    tags = station.get("tags", {})

    name = tags.get("name:en") or (tags.get("name") if is_english(tags.get("name", "")) else "Unnamed")
    brand = tags.get("brand:en") or (tags.get("brand") if is_english(tags.get("brand", "")) else "Unknown")
    address = (
        tags.get("addr:full:en")
        or tags.get("addr:street:en")
        or (tags.get("addr:full") if is_english(tags.get("addr:full", "")) else None)
        or (tags.get("addr:street") if is_english(tags.get("addr:street", "")) else None)
        or "Address Unknown"
    )

    # Skip if Urdu or doesn't match selected brand
    if not is_english(name) or not is_english(brand):
        continue
    if selected_brand != "All" and brand.strip() != selected_brand:
        continue

    # Save info
    filtered_stations.append({
        "name": name,
        "brand": brand,
        "address": address,
        "lat": lat,
        "lon": lon
    })

    # Custom icon if brand matches known logos (case-insensitive)
    brand_key = brand.strip().lower()
    if brand_key in brand_icons:
        icon = folium.CustomIcon(brand_icons[brand_key], icon_size=(30, 30))
    else:
        icon = DEFAULT_ICON

    popup_text = f"<b>{name}</b><br>Brand: {brand}<br>Address: {address}"
    folium.Marker([lat, lon], popup=popup_text, icon=icon).add_to(m)

# --- Show Map ---
st_folium(m, width=1000)

# --- Show Station Info ---
if filtered_stations:
    st.subheader(f"📋 Fuel Station Details ({selected_brand if selected_brand != 'All' else 'All Brands'})")
    for i, station in enumerate(filtered_stations, 1):
        st.markdown(f"**{i}. {station['name']}**  \nBrand: {station['brand']}  \nAddress: {station['address']}")
else:
    st.warning("No matching English-labeled fuel stations found.")
