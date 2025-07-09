import streamlit as st
import folium
from streamlit_folium import st_folium
import requests
from geopy.distance import geodesic
from datetime import datetime
import pandas as pd
import time
import logging

# -----------------------------
# Page Configuration
# -----------------------------

# PSO Color Theme
PSO_GREEN = "#006400"
PSO_YELLOW = "#FFD700"
PSO_BLUE = "#0057B7"
PSO_LIGHT_GREEN = "#90EE90"
PSO_BG_GRADIENT = f"background: linear-gradient(135deg, {PSO_GREEN} 0%, {PSO_BLUE} 50%, {PSO_YELLOW} 100%);"

# Page setup
st.set_page_config(
    page_title="Enhanced Land Use Finder",
    page_icon="🗺️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for professional styling
st.markdown("""
<style>
    .main-header {
        padding: 1.5rem;
        border-radius: 18px;
        background: linear-gradient(135deg, #006400 0%, #0057B7 50%, #FFD700 100%);
        box-shadow: 0 8px 32px rgba(0,0,0,0.12);
        margin-bottom: 2rem;
        text-align: center;
    }
    .main-title {
        color: #FFD700;
        font-weight: 900;
        letter-spacing: 2px;
        margin-bottom: 0.2em;
        font-size: 2.5rem;
    }
    .main-subtitle {
        color: white;
        font-size: 1.2rem;
        font-weight: 300;
    }
    .metric-card {
        background: white;
        padding: 1rem;
        border-radius: 10px;
        border-left: 4px solid #006400;
        box-shadow: 0 2px 8px rgba(0,0,0,0.1);
        margin: 0.5rem 0;
    }
    .fuel-station-card {
        background: linear-gradient(45deg, #f8f9fa, #ffffff);
        padding: 1rem;
        border-radius: 10px;
        border: 1px solid #e9ecef;
        margin: 0.5rem 0;
        box-shadow: 0 2px 4px rgba(0,0,0,0.05);
    }
    .stDataFrame thead tr th {
        background-color: #006400 !important;
        color: #FFD700 !important;
        font-weight: bold;
    }
    .stDataFrame tbody tr td {
        font-size: 1.1em;
    }
    .status-success {
        color: #28a745;
        font-weight: bold;
    }
    .status-error {
        color: #dc3545;
        font-weight: bold;
    }
    .status-warning {
        color: #ffc107;
        font-weight: bold;
    }
</style>
""", unsafe_allow_html=True)

# Main header
st.markdown(f"""
    <div class='main-header'>
        <h1 class='main-title'>Pakistan State Oil GIS</h1>
        <p class='main-subtitle'>Enhanced Land Use Finder & Fuel Station Analysis</p>
    </div>
""", unsafe_allow_html=True)

# -----------------------------
# Translation and Text Processing
# -----------------------------

def translate_urdu_to_english(text):
    """Translate common Urdu terms to English."""
    urdu_to_english = {
        # Common place names and terms
        'کراچی': 'Karachi',
        'لاہور': 'Lahore',
        'اسلام آباد': 'Islamabad',
        'فیصل آباد': 'Faisalabad',
        'ملتان': 'Multan',
        'حیدرآباد': 'Hyderabad',
        'راولپنڈی': 'Rawalpindi',
        'پشاور': 'Peshawar',
        'کوئٹہ': 'Quetta',
        'سکھر': 'Sukkur',
        
        # Fuel station terms
        'پیٹرول پمپ': 'Petrol Pump',
        'ایندھن اسٹیشن': 'Fuel Station',
        'گیس اسٹیشن': 'Gas Station',
        'پی ایس او': 'PSO',
        'شیل': 'Shell',
        'ٹوٹل': 'Total',
        'ایٹک': 'Attock',
        'حسکول': 'Hascol',
        
        # Land use terms
        'رہائشی علاقہ': 'Residential Area',
        'تجارتی علاقہ': 'Commercial Area',
        'صنعتی علاقہ': 'Industrial Area',
        'زرعی زمین': 'Agricultural Land',
        'پارک': 'Park',
        'اسپتال': 'Hospital',
        'اسکول': 'School',
        'مسجد': 'Mosque',
        'بازار': 'Market',
        'مال': 'Mall',
        
        # General terms
        'شمال': 'North',
        'جنوب': 'South',
        'مشرق': 'East',
        'مغرب': 'West',
        'فاصلہ': 'Distance',
        'کلومیٹر': 'Kilometer',
        'میٹر': 'Meter',
        'سڑک': 'Road',
        'گلی': 'Street',
        'محلہ': 'Neighborhood'
    }
    
    # Clean and translate text
    if not text or not isinstance(text, str):
        return text
    
    # Replace Urdu text with English
    translated = text
    for urdu, english in urdu_to_english.items():
        translated = translated.replace(urdu, english)
    
    return translated

def format_location_name(name):
    """Format location names for better presentation."""
    if not name:
        return "Unknown Location"
    
    # Translate if contains Urdu
    translated = translate_urdu_to_english(name)
    
    # Clean up common naming issues
    cleaned = translated.strip()
    
    # Remove common prefixes/suffixes that might be redundant
    prefixes_to_remove = ['Fuel Station', 'Petrol Pump', 'Gas Station']
    for prefix in prefixes_to_remove:
        if cleaned.startswith(prefix + ' '):
            cleaned = cleaned[len(prefix + ' '):]
        elif cleaned.endswith(' ' + prefix):
            cleaned = cleaned[:-len(' ' + prefix)]
    
    # Capitalize properly
    if cleaned:
        cleaned = ' '.join(word.capitalize() for word in cleaned.split())
    
    return cleaned if cleaned else "Unnamed Location"

def create_info_card(title, content, icon="ℹ️", color=PSO_GREEN):
    """Create a professional information card."""
    return f"""
    <div style="
        background: linear-gradient(135deg, #ffffff 0%, #f8f9fa 100%);
        border-left: 4px solid {color};
        border-radius: 8px;
        padding: 1.5rem;
        margin: 1rem 0;
        box-shadow: 0 2px 8px rgba(0,0,0,0.1);
    ">
        <div style="display: flex; align-items: center; margin-bottom: 0.5rem;">
            <span style="font-size: 1.5rem; margin-right: 0.5rem;">{icon}</span>
            <h3 style="margin: 0; color: {color}; font-weight: 600;">{title}</h3>
        </div>
        <div style="color: #333; line-height: 1.6;">{content}</div>
    </div>
    """

# -----------------------------
# Helper Functions
# -----------------------------

def safe_api_call(func, *args, **kwargs):
    """Safely call API with error handling and retries."""
    max_retries = 3
    for attempt in range(max_retries):
        try:
            return func(*args, **kwargs)
        except requests.exceptions.RequestException as e:
            if attempt < max_retries - 1:
                time.sleep(2 ** attempt)  # Exponential backoff
                continue
            else:
                st.error(f"API call failed after {max_retries} attempts: {str(e)}")
                return None
        except Exception as e:
            st.error(f"Unexpected error: {str(e)}")
            return None

def overpass_query(query):
    """Query Overpass API with error handling."""
    url = "https://overpass-api.de/api/interpreter"
    try:
        response = requests.post(
            url, 
            data=query, 
            headers={"Content-Type": "text/plain"},
            timeout=30
        )
        response.raise_for_status()
        return response.json()
    except requests.exceptions.Timeout:
        st.error("API request timed out. Please try again.")
        return None
    except requests.exceptions.HTTPError as e:
        st.error(f"HTTP error occurred: {e}")
        return None
    except Exception as e:
        st.error(f"Error querying Overpass API: {str(e)}")
        return None

def calculate_distance_km(coord1, coord2):
    """Calculate distance between two coordinates in kilometers."""
    try:
        return round(geodesic(coord1, coord2).km, 3)
    except Exception as e:
        st.error(f"Error calculating distance: {str(e)}")
        return 0

def validate_coordinates(lat, lon):
    """Validate latitude and longitude values."""
    if not (-90 <= lat <= 90):
        return False, "Latitude must be between -90 and 90"
    if not (-180 <= lon <= 180):
        return False, "Longitude must be between -180 and 180"
    return True, "Valid coordinates"

# -----------------------------
# Fuel Brand Configuration
# -----------------------------

FUEL_BRAND_ICONS = {
    "PSO": {"emoji": "🟢", "color": "green"},
    "Shell": {"emoji": "🐚", "color": "yellow"},
    "Total": {"emoji": "🔴", "color": "red"},
    "Attock": {"emoji": "🟠", "color": "orange"},
    "Hascol": {"emoji": "🔵", "color": "blue"},
    "GO": {"emoji": "🟣", "color": "purple"},
    "Byco": {"emoji": "🟤", "color": "brown"},
    "Unknown": {"emoji": "⛽", "color": "gray"}
}

def get_brand_info(brand):
    """Get brand icon and color information."""
    for key in FUEL_BRAND_ICONS:
        if key.lower() in brand.lower():
            return FUEL_BRAND_ICONS[key]
    return FUEL_BRAND_ICONS["Unknown"]

# -----------------------------
# Sidebar Configuration
# -----------------------------

st.sidebar.header("🎯 Location Input")

# Coordinate inputs with validation
lat = st.sidebar.number_input(
    "Latitude", 
    format="%.6f", 
    value=33.6844,  # Default to Islamabad
    min_value=-90.0,
    max_value=90.0,
    help="Enter latitude between -90 and 90"
)

lon = st.sidebar.number_input(
    "Longitude", 
    format="%.6f", 
    value=73.0479,  # Default to Islamabad
    min_value=-180.0,
    max_value=180.0,
    help="Enter longitude between -180 and 180"
)

# Validate coordinates
is_valid, validation_message = validate_coordinates(lat, lon)
if not is_valid:
    st.sidebar.error(validation_message)

# Radius input
radius = st.sidebar.number_input(
    "Search Radius (meters)", 
    min_value=100, 
    max_value=5000, 
    value=1000, 
    step=100,
    help="Search radius in meters (100-5000m)"
)

# Quick location selector
st.sidebar.subheader("🏙️ Quick Locations")
quick_locations = {
    "Custom": (lat, lon),
    "Karachi": (24.8607, 67.0011),
    "Lahore": (31.5804, 74.3587),
    "Islamabad": (33.6844, 73.0479),
    "Faisalabad": (31.4504, 73.1350),
    "Multan": (30.1798, 71.4924),
    "Hyderabad": (25.3960, 68.3578)
}

selected_city = st.sidebar.selectbox(
    "Select City", 
    list(quick_locations.keys()),
    index=2  # Default to Islamabad
)

if selected_city != "Custom":
    lat, lon = quick_locations[selected_city]
    st.sidebar.success(f"Selected: {selected_city}")

# PSO branding
st.sidebar.markdown("---")
st.sidebar.markdown(
    "<div style='text-align:center; font-size:2rem; padding:1rem;'>🟢🟡🔵</div>", 
    unsafe_allow_html=True
)
st.sidebar.markdown(
    "<div style='text-align:center; color:#006400; font-weight:bold;'>Pakistan State Oil</div>", 
    unsafe_allow_html=True
)

# -----------------------------
# Main Functions
# -----------------------------

def find_fuel_stations(lat, lon, radius):
    """Find fuel stations within specified radius."""
    if not is_valid:
        return []
    
    query = f"""
    [out:json][timeout:30];
    (
      node["amenity"="fuel"](around:{radius},{lat},{lon});
      way["amenity"="fuel"](around:{radius},{lat},{lon});
    );
    out center;
    """
    
    data = safe_api_call(overpass_query, query)
    if not data:
        return []
    
    stations = []
    for el in data.get("elements", []):
        try:
            # Handle both nodes and ways
            if "lat" in el and "lon" in el:
                element_lat, element_lon = el["lat"], el["lon"]
            elif "center" in el:
                element_lat, element_lon = el["center"]["lat"], el["center"]["lon"]
            else:
                continue
                
            tags = el.get("tags", {})
            raw_name = tags.get("name:en") or tags.get("name") or "Unnamed Fuel Station"
            raw_brand = tags.get("brand", "Unknown")
            raw_operator = tags.get("operator", "")
            
            # Translate and format names
            name = format_location_name(raw_name)
            brand = format_location_name(raw_brand) if raw_brand != "Unknown" else "Unknown"
            operator = format_location_name(raw_operator) if raw_operator else ""
            
            # Use operator if brand is unknown
            if brand == "Unknown" and operator:
                brand = operator
            
            coord = (element_lat, element_lon)
            distance = calculate_distance_km((lat, lon), coord)
            
            # Only include stations within the radius
            if distance <= radius / 1000:
                stations.append({
                    "name": name,
                    "lat": element_lat,
                    "lon": element_lon,
                    "distance": distance,
                    "brand": brand,
                    "operator": operator,
                    "raw_name": raw_name,  # Keep original for reference
                    "address": tags.get("addr:full", tags.get("addr:street", ""))
                })
        except Exception as e:
            continue  # Skip problematic entries
    
    # Sort by distance
    stations.sort(key=lambda x: x["distance"])
    return stations

def get_land_use(lat, lon, radius):
    """Analyze land use within specified radius."""
    if not is_valid:
        return {}
    
    query = f"""
    [out:json][timeout:30];
    (
      way["landuse"](around:{radius},{lat},{lon});
      relation["landuse"](around:{radius},{lat},{lon});
    );
    out body;
    """
    
    data = safe_api_call(overpass_query, query)
    if not data:
        return {}
    
    land_counts = {}
    for el in data.get("elements", []):
        try:
            landuse = el.get("tags", {}).get("landuse")
            if landuse:
                land_counts[landuse] = land_counts.get(landuse, 0) + 1
        except Exception:
            continue
    
    return land_counts

def simulate_traffic():
    """Simulate traffic based on current time."""
    try:
        hour = datetime.now().hour
        if 7 <= hour <= 9 or 17 <= hour <= 19:
            return "🔴 Heavy", "Peak hours traffic"
        elif 10 <= hour <= 16:
            return "🟡 Moderate", "Normal business hours"
        else:
            return "🟢 Light", "Off-peak hours"
    except Exception:
        return "🔘 Unknown", "Unable to determine"

def estimate_population(land_data):
    """Estimate population based on land use data."""
    try:
        residential = land_data.get("residential", 0)
        commercial = land_data.get("commercial", 0)
        industrial = land_data.get("industrial", 0)
        
        # Improved population estimation
        base_population = residential * 150  # Assume 150 people per residential unit
        commercial_factor = commercial * 50   # Commercial areas attract people
        industrial_factor = industrial * 30   # Industrial areas have workers
        
        total_estimate = base_population + commercial_factor + industrial_factor
        return max(total_estimate, 0)
    except Exception:
        return 0

# -----------------------------
# Map Creation
# -----------------------------

def create_map(lat, lon, radius):
    """Create the main map with markers and overlays."""
    # Create map
    my_map = folium.Map(
        location=[lat, lon], 
        zoom_start=15, 
        tiles="OpenStreetMap"
    )
    
    # Add main location marker
    folium.Marker(
        location=[lat, lon],
        tooltip="📍 Selected Location",
        icon=folium.Icon(color="red", icon="star")
    ).add_to(my_map)
    
    # Add search radius circle
    folium.Circle(
        location=[lat, lon],
        radius=radius,
        color=PSO_GREEN,
        fill=True,
        fill_opacity=0.15,
        weight=2,
        tooltip=f"Search radius: {radius}m"
    ).add_to(my_map)
    
    return my_map

# -----------------------------
# Main Application Logic
# -----------------------------

# Initialize session state
if "fuel_stations" not in st.session_state:
    st.session_state.fuel_stations = []
if "land_data" not in st.session_state:
    st.session_state.land_data = {}

# Create main map
if is_valid:
    main_map = create_map(lat, lon, radius)
    
    # Action buttons
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("🔍 Search Location", type="primary"):
            st.success(f"📍 Location loaded: {lat:.6f}, {lon:.6f}")
    
    with col2:
        if st.button("⛽ Find Fuel Stations", type="secondary"):
            with st.spinner("Searching for fuel stations..."):
                stations = find_fuel_stations(lat, lon, radius)
                st.session_state.fuel_stations = stations
                st.success(f"Found {len(stations)} fuel stations within {radius}m")
    
    with col3:
        if st.button("🏘️ Analyze Land Use", type="secondary"):
            with st.spinner("Analyzing land use..."):
                land_data = get_land_use(lat, lon, radius)
                st.session_state.land_data = land_data
                st.success("Land use analysis completed")
    
    # Display results
    if st.session_state.fuel_stations:
        st.subheader("⛽ Fuel Stations Analysis")
        
        # Create enhanced info cards for top 3 stations
        if len(st.session_state.fuel_stations) > 0:
            st.markdown("### 🎯 Nearest Fuel Stations")
            
            cols = st.columns(min(3, len(st.session_state.fuel_stations)))
            for i, station in enumerate(st.session_state.fuel_stations[:3]):
                with cols[i]:
                    brand_info = get_brand_info(station["brand"])
                    address_info = f"<br><small>📍 {station['address']}</small>" if station.get('address') else ""
                    
                    card_content = f"""
                    <div style="text-align: center;">
                        <div style="font-size: 2rem; margin-bottom: 0.5rem;">{brand_info['emoji']}</div>
                        <h4 style="margin: 0.5rem 0; color: {PSO_GREEN};">{station['name']}</h4>
                        <p style="margin: 0.25rem 0;"><strong>Brand:</strong> {station['brand']}</p>
                        <p style="margin: 0.25rem 0;"><strong>Distance:</strong> {station['distance']} km</p>
                        {address_info}
                    </div>
                    """
                    
                    st.markdown(create_info_card(
                        f"Station {i+1}",
                        card_content,
                        brand_info['emoji'],
                        PSO_GREEN
                    ), unsafe_allow_html=True)
        
        # Add fuel station markers to map
        for station in st.session_state.fuel_stations:
            brand_info = get_brand_info(station["brand"])
            
            # Create detailed popup with translated information
            popup_content = f"""
            <div style="min-width: 200px;">
                <h4>{brand_info['emoji']} {station['name']}</h4>
                <p><strong>Brand:</strong> {station['brand']}</p>
                <p><strong>Distance:</strong> {station['distance']} km</p>
                <p><strong>Coordinates:</strong> {station['lat']:.6f}, {station['lon']:.6f}</p>
                {f"<p><strong>Address:</strong> {station['address']}</p>" if station.get('address') else ""}
                <hr>
                <small><em>Original Name:</em> {station['raw_name']}</small>
            </div>
            """
            
            folium.Marker(
                location=[station["lat"], station["lon"]],
                popup=folium.Popup(popup_content, max_width=300),
                tooltip=f"{brand_info['emoji']} {station['name']} ({station['distance']}km)",
                icon=folium.Icon(color=brand_info["color"], icon="tint")
            ).add_to(main_map)
        
        # Create enhanced DataFrame for display
        st.markdown("### 📊 Complete Station List")
        df_stations = pd.DataFrame([
            {
                "🏪 Brand": f"{get_brand_info(s['brand'])['emoji']} {s['brand']}",
                "📍 Station Name": s["name"],
                "📏 Distance": f"{s['distance']} km",
                "🗺️ Coordinates": f"{s['lat']:.6f}, {s['lon']:.6f}",
                "🏠 Address": s.get('address', 'N/A'),
                "📝 Original Name": s['raw_name']
            }
            for s in st.session_state.fuel_stations
        ])
        
        st.dataframe(df_stations, use_container_width=True)
        
        # Enhanced statistics with visual cards
        st.markdown("### 📈 Station Analytics")
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            total_stations = len(st.session_state.fuel_stations)
            st.markdown(create_info_card(
                "Total Stations",
                f"<h2 style='text-align: center; color: {PSO_GREEN}; margin: 0;'>{total_stations}</h2>",
                "🏪",
                PSO_GREEN
            ), unsafe_allow_html=True)
        
        with col2:
            if st.session_state.fuel_stations:
                closest = min(st.session_state.fuel_stations, key=lambda x: x["distance"])
                st.markdown(create_info_card(
                    "Nearest Station",
                    f"<div style='text-align: center;'><h3 style='color: {PSO_BLUE}; margin: 0;'>{closest['distance']} km</h3><p style='margin: 0.5rem 0;'>{closest['name']}</p></div>",
                    "📍",
                    PSO_BLUE
                ), unsafe_allow_html=True)
        
        with col3:
            brands = set(s["brand"] for s in st.session_state.fuel_stations)
            st.markdown(create_info_card(
                "Unique Brands",
                f"<h2 style='text-align: center; color: {PSO_YELLOW}; margin: 0;'>{len(brands)}</h2>",
                "🏷️",
                PSO_YELLOW
            ), unsafe_allow_html=True)
        
        with col4:
            avg_distance = sum(s["distance"] for s in st.session_state.fuel_stations) / len(st.session_state.fuel_stations)
            st.markdown(create_info_card(
                "Average Distance",
                f"<h2 style='text-align: center; color: {PSO_GREEN}; margin: 0;'>{avg_distance:.2f} km</h2>",
                "📊",
                PSO_GREEN
            ), unsafe_allow_html=True)
        
        # Brand distribution
        if len(brands) > 1:
            st.markdown("### 🎯 Brand Distribution")
            brand_counts = {}
            for station in st.session_state.fuel_stations:
                brand = station["brand"]
                brand_counts[brand] = brand_counts.get(brand, 0) + 1
            
            brand_df = pd.DataFrame([
                {"Brand": f"{get_brand_info(brand)['emoji']} {brand}", "Count": count}
                for brand, count in sorted(brand_counts.items(), key=lambda x: x[1], reverse=True)
            ])
            
            col1, col2 = st.columns(2)
            with col1:
                st.dataframe(brand_df, use_container_width=True)
            with col2:
                # Create a simple text-based chart
                chart_content = ""
                for brand, count in sorted(brand_counts.items(), key=lambda x: x[1], reverse=True):
                    emoji = get_brand_info(brand)['emoji']
                    percentage = (count / len(st.session_state.fuel_stations)) * 100
                    bar = "█" * int(percentage / 5)  # Scale bar
                    chart_content += f"{emoji} {brand}: {bar} {count} ({percentage:.1f}%)<br>"
                
                st.markdown(create_info_card(
                    "Distribution Chart",
                    chart_content,
                    "📊",
                    PSO_BLUE
                ), unsafe_allow_html=True)
    
    if st.session_state.land_data:
        st.subheader("🏘️ Land Use Analysis")
        
        if st.session_state.land_data:
            # Create enhanced land use cards
            st.markdown("### 🏗️ Land Use Distribution")
            
            # Sort land use by count
            sorted_land_use = sorted(st.session_state.land_data.items(), key=lambda x: x[1], reverse=True)
            
            # Display top land use types as cards
            if len(sorted_land_use) > 0:
                cols = st.columns(min(4, len(sorted_land_use)))
                
                land_use_icons = {
                    'residential': '🏠',
                    'commercial': '🏪',
                    'industrial': '🏭',
                    'retail': '🛍️',
                    'forest': '🌲',
                    'farmland': '🌾',
                    'grass': '🌱',
                    'cemetery': '⛪',
                    'recreation_ground': '⚽',
                    'education': '🎓',
                    'healthcare': '🏥',
                    'religious': '🕌'
                }
                
                for i, (land_type, count) in enumerate(sorted_land_use[:4]):
                    with cols[i]:
                        icon = land_use_icons.get(land_type, '🏗️')
                        formatted_name = translate_urdu_to_english(land_type.replace('_', ' ').title())
                        
                        card_content = f"""
                        <div style="text-align: center;">
                            <div style="font-size: 3rem; margin-bottom: 0.5rem;">{icon}</div>
                            <h3 style="margin: 0.5rem 0; color: {PSO_GREEN};">{count}</h3>
                            <p style="margin: 0; font-weight: 500;">{formatted_name}</p>
                        </div>
                        """
                        
                        st.markdown(create_info_card(
                            f"{formatted_name}",
                            card_content,
                            icon,
                            PSO_GREEN
                        ), unsafe_allow_html=True)
            
            # Create comprehensive DataFrame for land use
            df_land = pd.DataFrame([
                {
                    "🏗️ Land Use Type": f"{land_use_icons.get(k, '🏗️')} {translate_urdu_to_english(k.replace('_', ' ').title())}",
                    "📊 Count": v,
                    "📈 Percentage": f"{(v / sum(st.session_state.land_data.values()) * 100):.1f}%"
                }
                for k, v in sorted_land_use
            ])
            
            st.markdown("### 📊 Detailed Land Use Breakdown")
            col1, col2 = st.columns([2, 1])
            
            with col1:
                st.dataframe(df_land, use_container_width=True)
            
            with col2:
                # Enhanced statistics
                pop_estimate = estimate_population(st.session_state.land_data)
                
                st.markdown(create_info_card(
                    "Population Estimate",
                    f"<h2 style='text-align: center; color: {PSO_BLUE}; margin: 0;'>{pop_estimate:,}</h2><p style='text-align: center; margin: 0.5rem 0;'>Based on land use analysis</p>",
                    "👥",
                    PSO_BLUE
                ), unsafe_allow_html=True)
                
                if st.session_state.land_data:
                    dominant = max(st.session_state.land_data, key=st.session_state.land_data.get)
                    dominant_icon = land_use_icons.get(dominant, '🏗️')
                    dominant_name = translate_urdu_to_english(dominant.replace('_', ' ').title())
                    
                    st.markdown(create_info_card(
                        "Dominant Land Use",
                        f"<div style='text-align: center;'><div style='font-size: 2rem;'>{dominant_icon}</div><h3 style='color: {PSO_GREEN}; margin: 0.5rem 0;'>{dominant_name}</h3></div>",
                        dominant_icon,
                        PSO_GREEN
                    ), unsafe_allow_html=True)
                
                # Area characteristics
                area_type = "Urban" if any(k in st.session_state.land_data for k in ['commercial', 'residential', 'industrial']) else "Rural"
                density = "High" if pop_estimate > 1000 else "Medium" if pop_estimate > 100 else "Low"
                
                characteristics = f"""
                <div style="text-align: center;">
                    <p><strong>Area Type:</strong> {area_type}</p>
                    <p><strong>Density:</strong> {density}</p>
                    <p><strong>Total Categories:</strong> {len(st.session_state.land_data)}</p>
                </div>
                """
                
                st.markdown(create_info_card(
                    "Area Characteristics",
                    characteristics,
                    "🌍",
                    PSO_YELLOW
                ), unsafe_allow_html=True)
        else:
            st.info("No land use data found for this location.")
    
    # Enhanced traffic simulation
    st.subheader("🚦 Traffic Analysis")
    traffic_status, traffic_desc = simulate_traffic()
    
    col1, col2 = st.columns(2)
    with col1:
        st.markdown(create_info_card(
            "Current Traffic Level",
            f"<div style='text-align: center;'><h2 style='margin: 0;'>{traffic_status}</h2><p style='margin: 0.5rem 0;'>{traffic_desc}</p></div>",
            "🚦",
            PSO_BLUE
        ), unsafe_allow_html=True)
    
    with col2:
        # Additional traffic insights
        hour = datetime.now().hour
        next_change = ""
        if 7 <= hour <= 9:
            next_change = "Traffic will ease after 9 AM"
        elif 17 <= hour <= 19:
            next_change = "Traffic will ease after 7 PM"
        elif hour < 7:
            next_change = "Morning rush starts at 7 AM"
        else:
            next_change = "Evening rush starts at 5 PM"
        
        traffic_insights = f"""
        <div style="text-align: center;">
            <p><strong>Current Time:</strong> {datetime.now().strftime('%I:%M %p')}</p>
            <p><strong>Next Change:</strong> {next_change}</p>
            <p><strong>Best Time to Travel:</strong> 10 AM - 4 PM</p>
        </div>
        """
        
        st.markdown(create_info_card(
            "Traffic Insights",
            traffic_insights,
            "💡",
            PSO_YELLOW
        ), unsafe_allow_html=True)
    
    # Display map
    st.subheader("🗺️ Interactive Map")
    st_data = st_folium(main_map, width=1000, height=600, returned_objects=["last_clicked"])
    
    # Handle map clicks
    if st_data["last_clicked"]:
        clicked_lat = st_data["last_clicked"]["lat"]
        clicked_lon = st_data["last_clicked"]["lng"]
        st.info(f"Clicked coordinates: {clicked_lat:.6f}, {clicked_lon:.6f}")

else:
    st.error("Please enter valid coordinates to continue.")
    st.stop()

# Footer
st.markdown("---")
st.markdown(
    "<div style='text-align:center; color:#666; padding:1rem;'>"
    "Pakistan State Oil GIS System | Enhanced Land Use Finder"
    "</div>", 
    unsafe_allow_html=True
)