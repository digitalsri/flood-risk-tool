import streamlit as st
import pandas as pd
import folium
from streamlit_folium import folium_static
import plotly.graph_objects as go
import time

# --- Page Configuration ---
st.set_page_config(
    page_title="Flood Risk Assessment Tool",
    page_icon="🌊",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# --- Custom CSS for Enhanced UI ---
st.markdown("""
<style>
    [data-testid="stSidebar"] { display: none; }

    .main-header {
    text-align: center; 
    padding: 1.5rem 1rem;
    background: linear-gradient(90deg, #1e3c72 0%, #2a5298 100%);
    color: white; 
    border-radius: 10px; 
    margin-bottom: 2rem;
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    }

.main-header h1 {
    font-size: 2.2rem;
    font-weight: 700;
    margin: 0 0 0.75rem 0;
    letter-spacing: -0.5px;
    line-height: 1.2;
    }

.main-header p {
    font-size: 1rem;
    margin: 0;
    opacity: 0.95;
    font-weight: 400;
    max-width: 600px;
    line-height: 1.4;
    text-align: center;
    }        

   
    div[data-testid="stHorizontalBlock"] {
        display: flex;
        align-items: center;
    }
    div[data-testid="stHorizontalBlock"] > div:first-child {
        flex-grow: 1; margin-right: 8px;
    }
    div[data-testid="stHorizontalBlock"] > div:not(:first-child) {
        flex-grow: 0;
    }

    .location-header {
        font-size: 1.5rem; font-weight: bold; color: #1e3c72;
        padding: 1rem; background-color: #f8f9fa; border: 1px solid #e9ecef;
        border-radius: 10px; margin-bottom: 1rem; display: flex; align-items: center;
    }
    
    .road-name { font-size: 1.1rem; color: #5a5a5a; font-weight: 600; display: block; }
    
    .kpi-container {
        text-align: center; padding: 1rem;
        display: flex; flex-direction: column; justify-content: center;
        min-height: 192px; /* Added to match the height of gauge chart boxes */
    }
    
    .kpi-label {
        font-size: 0.8rem; color: #666; text-transform: uppercase;
        font-weight: 600; letter-spacing: 0.5px;
    }
    
    .kpi-value { font-size: 2.5rem; font-weight: bold; margin: 15px 0; }
    
    .kpi-subtitle {
        font-size: 0.9rem; color: #666; font-weight: bold;
        text-align: center; padding-bottom: 5px;
    }
    
    .final-recommendation {
        font-size: 1.1rem; font-weight: 600; color: #1e3c72;
        text-align: center; margin-top: 1.5rem; padding: 0.75rem;
        background-color: #f8f9fa; border-radius: 10px; border: 1px solid #e9ecef;
    }

    .risk-indicator-container {
    display: flex; justify-content: center; align-items: center;
    border-radius: 10px; padding: 1rem;
    margin-top: 1.5rem; border: 1px solid #e9ecef;
    }
    
    .indicator {
        display: flex; align-items: center; font-size: 1.1rem;
        font-weight: 600; text-align: center; margin: 0 1.5rem;
    }

    .indicator-value { font-size: 1.1rem; font-weight: bold; margin-left: 8px; }
    
    .icon-svg { width: 24px; height: 24px; margin-right: 12px; }
    .indicator-icon-svg { width: 20px; height: 20px; margin-right: 8px; }

    .stButton > button {
            border-radius: 8px; padding: 0.75rem; font-weight: bold;
            transition: all 0.3s; width: 100% !important; border: 1px solid #d1d1d1;
        }
        .stButton > button[kind="primary"] { background-color: #2a5298; color: white; border: none; }
        .stButton > button[kind="secondary"] { background-color: #ffffff; color: #333; }
        
        /* Ensure columns have minimal gaps */
        .stColumns > div {
            padding-left: 0.25rem !important;
            padding-right: 0.25rem !important;
        }
        
        /* Ensure horizontal blocks align properly */
        div[data-testid="stHorizontalBlock"] > div {
            display: flex;
            align-items: center;
        }
                           
    @media (max-width: 768px) {
    .main-header {
        padding: 1.25rem 0.75rem;}
    
    .main-header h1 {
        font-size: 1.8rem;
        margin-bottom: 0.5rem;}
    
    .main-header p {
        font-size: 0.9rem;
        padding: 0 0.5rem;}
    }

    @media (max-width: 480px) {
    .main-header h1 {
        font-size: 1.6rem;}
    
    .main-header p {
        font-size: 0.85rem;}
    }        

</style>
""", unsafe_allow_html=True)

# --- Data Loading and Processing ---

@st.cache_data
def load_data(file_path="flood_risk_data.csv.gz"):
    try:
        # Check if file exists first
        import os
        if not os.path.exists(file_path):
            st.error(f"❌ Data file '{file_path}' not found. Please ensure the file is uploaded to your repository.")
            return {}
            
        df = pd.read_csv(file_path, compression='gzip', dtype={'POSTAL': str})
        
        if df.empty:
            st.error("Data file is empty. Please check your data.")
            return {}
            
        df['POSTAL'] = df['POSTAL'].str.zfill(6)
        agg_logic = {
            "LATITUDE": "first",
            "LONGITUDE": "first", 
            "ROAD_NAME": "first",
            "ADDRESS": "first",
            "Flood_DEPTH_BASELINE": "mean",
            "Flood_DEPTH_RCP": "mean",
            "Flood_PRONE": "max",
            "HOTSPOT": "max",
        }
        processed_df = df.groupby("POSTAL", as_index=False).agg(agg_logic)
        for col in ['Flood_DEPTH_BASELINE', 'Flood_DEPTH_RCP']:
            processed_df[col] = processed_df[col].round(2)
            
        data_dict = {row['POSTAL']: row.to_dict() for _, row in processed_df.iterrows()}
                   
        return data_dict
        
    except Exception as e:
        st.error(f"Error loading data: {str(e)}")
        st.info("Please check that your data file is properly formatted and try again.")
        return {}

# --- Icon & Wording Definitions ---
HEADER_ICON = """<svg class="icon-svg" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 16 16" fill="#2a5298"><path d="M8 16s6-5.686 6-10A6 6 0 0 0 2 6c0 4.314 6 10 6 10zm0-7a3 3 0 1 1 0-6 3 3 0 0 1 0 6z"/></svg>"""
FLOOD_PRONE_ICON = """<svg class="indicator-icon-svg" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 16 16" fill="#d9534f"><path d="M5.072.56C6.157.265 7.31 0 8 0s1.843.265 2.928.56c1.11.3 2.229.655 2.887 1.177.659.522 1.096 1.145 1.096 1.876V8.5c0 .92-.326 1.78-1.096 2.447-.659.66-1.777 1.01-2.887 1.311A48.343 48.343 0 0 1 8 12.5c-1.125 0-2.31-.078-3.372-.24-1.065-.163-2.158-.5-2.887-1.177C1.053 10.42.5 9.473.5 8.5V3.613c0-.73.437-1.354 1.096-1.876.66-.522 1.778-.877 2.887-1.177zM8.5 7.5a.5.5 0 0 1-1 0v-3a.5.5 0 0 1 1 0v3zm0 3a.5.5 0 0 1-1 0v-1a.5.5 0 0 1 1 0v1z"/></svg>"""
FLOOD_HOTSPOT_ICON = """<svg class="indicator-icon-svg" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 16 16" fill="#2a5298"><path d="M12.166 8.94c-.524 1.062-1.234 2.12-1.96 3.07A31.493 31.493 0 0 1 8 14.58a31.481 31.481 0 0 1-2.206-2.57c-.726-.95-1.436-2.008-1.96-3.07C3.304 7.867 3 6.862 3 6a5 5 0 0 1 10 0c0 .862-.305 1.867-.834 2.94zM8 16s6-5.686 6-10A6 6 0 0 0 2 6c0 4.314 6 10 6 10z"/><path d="M8 9a1 1 0 1 1 0-2 1 1 0 0 1 0 2z"/></svg>"""

# --- Charting & Risk Classification ---
def get_risk_class(depth):
    if depth < 0.5: return "Low", "#50d890"
    elif depth <= 1.0: return "Medium", "#ffc26f"
    else: return "High", "#ff595e"

def create_kpi_gauge(value):
    _, color = get_risk_class(value)
    fig = go.Figure(go.Indicator(
        mode="gauge+number", value=value,
        number={'suffix': "m", 'font': {'size': 28, 'color': "#1e3c72"}},
        gauge={'axis': {'range': [0, 1.5], 'tickvals': [0.5, 1], 'ticktext': ['0.5', '1']},
               'bar': {'color': color, 'thickness': 0.4},
               'steps': [{'range': [0, 0.5], 'color': '#e8f5e8'}, {'range': [0.5, 1.0], 'color': '#fff3e0'}, {'range': [1.0, 1.5], 'color': '#ffebee'}]},
    ))
    fig.update_layout(height=120, margin=dict(l=10, r=10, t=0, b=0), paper_bgcolor='rgba(0,0,0,0)')
    return fig

def create_flood_map(info, rcp):
    m = folium.Map(location=[info.get('LATITUDE', 1.29), info.get('LONGITUDE', 103.85)], zoom_start=16, tiles='OpenStreetMap')
    _, rcp_color = get_risk_class(rcp)
    folium.Marker([info.get('LATITUDE'), info.get('LONGITUDE')], icon=folium.Icon(color='blue', icon='home')).add_to(m)
    folium.Circle([info.get('LATITUDE'), info.get('LONGITUDE')], radius=200, color=rcp_color, fillColor=rcp_color, fillOpacity=0.3).add_to(m)
    return m

# --- Main Application Logic ---
def main():
    st.markdown("""
    <div class='main-header'>
        <h1>Flood Risk Assessment Tool</h1>
        <p>Enter a six-digit Singapore postal code to assess location-specific flood risk</p>
    </div>
    """, unsafe_allow_html=True)
    
    postal_data = load_data()
    
    def clear_state():
        st.session_state.postal_input, st.session_state.show_results = "", False

    if 'show_results' not in st.session_state: st.session_state.show_results = False
    if 'postal_input' not in st.session_state: st.session_state.postal_input = ""
    
    _, mid_col, _ = st.columns([1.5, 3, 1.5])
    with mid_col:
            in_col, an_col, cl_col = st.columns([4, 1.2, 1])
            with in_col:
                st.text_input("Postal Code", key="postal_input", placeholder="Enter Postal Code...", max_chars=6, label_visibility="collapsed")
            with an_col:
                analyze_button = st.button("Analyze", type="primary", use_container_width=True)
            with cl_col:
                st.button("Clear", type="secondary", on_click=clear_state, use_container_width=True)    

    if analyze_button:
        if st.session_state.postal_input.isdigit() and len(st.session_state.postal_input) == 6:
            st.session_state.show_results = True
        else:
            st.warning("Please enter a valid six-digit postal code.")
            st.session_state.show_results = False

    if not st.session_state.show_results:
        st.info("Your flood risk report will appear here. Enter a postal code above to begin.")
        return

    with st.spinner("Analyzing risk..."):
        postal_code = st.session_state.postal_input
        if postal_code in postal_data:
            info = postal_data[postal_code]
            baseline_depth, rcp85_depth = info.get('Flood_DEPTH_BASELINE', 0), info.get('Flood_DEPTH_RCP', 0)
            
            st.markdown("---")
            st.markdown(f"<div class='location-header'>{HEADER_ICON}<div>Flood Risk Assessment for Singapore {postal_code}<span class='road-name'>{info.get('ROAD_NAME', '')}</span></div></div>", unsafe_allow_html=True)
            
            col1, col2, col3 = st.columns(3)
            with col1:
                with st.container(border=True):
                    st.markdown("<div class='kpi-label'>BASELINE FLOOD DEPTH</div>", unsafe_allow_html=True, help="Flood depth based on current or historical climate conditions.")
                    st.plotly_chart(create_kpi_gauge(baseline_depth), use_container_width=True, key="baseline_gauge")
                    risk, color = get_risk_class(baseline_depth)
                    st.markdown(f'<div class="kpi-subtitle" style="color: {color};">{risk} Risk</div>', unsafe_allow_html=True)

            with col2:
                with st.container(border=True):
                    st.markdown("<div class='kpi-label'>RCP8.5 FLOOD DEPTH</div>", unsafe_allow_html=True, help="A future high-risk scenario which assumes worst case climate impacts.")
                    st.plotly_chart(create_kpi_gauge(rcp85_depth), use_container_width=True, key="rcp85_gauge")
                    risk, color = get_risk_class(rcp85_depth)
                    st.markdown(f'<div class="kpi-subtitle" style="color: {color};">{risk} Risk</div>', unsafe_allow_html=True)
            
            with col3:
                with st.container(border=True):
                    risk, color = get_risk_class(rcp85_depth)
                    st.markdown(f'<div class="kpi-container"><div class="kpi-label">OVERALL RISK</div><div class="kpi-value" style="color: {color};">{risk}</div><div class="kpi-subtitle" style="text-align:center; font-weight:normal;">Under RCP8.5 Scenario</div></div>', unsafe_allow_html=True)

            change = rcp85_depth - baseline_depth
            change_color = "#50d890" if change < 0 else "#ff595e"
            arrow = "↓" if change < 0 else "↑"
            st.markdown(f'<div style="text-align: center; font-weight: 600; color: #666; margin-top: 0.5rem;" title="Future flood depth increase vs. today. Higher value means greater flood risk at this location.">RISK CHANGE <span style="color: {change_color}; font-weight: bold; margin-left: 10px;">{arrow} {abs(change):.2f}m</span></div>', unsafe_allow_html=True)
            
            risk, _ = get_risk_class(rcp85_depth)
            if risk == "High": rec_text = "<b>Recommendation:</b> Whoa, high risk! 🌊 Time to review flood insurance and mitigation options. Stay informed about local flood warnings."
            elif risk == "Medium": rec_text = "<b>Recommendation:</b> Medium risk—stay vigilant! 👀 Monitor local flood advisories, especially during heavy rain or storm seasons."
            else: rec_text = "<b>Recommendation:</b> Low risk—enjoy the peace of mind, but keep an eye on weather reports just in case. 🌤️"
            st.markdown(f'<div class="final-recommendation">{rec_text}</div>', unsafe_allow_html=True)

            is_prone, is_hotspot = info.get("Flood_PRONE") == 1, info.get("HOTSPOT") == 1
            prone_color = "#d9534f" if is_prone else "#50d890"
            hotspot_color = "#d9534f" if is_hotspot else "#50d890"
            prone_text, hotspot_text = ("Yes" if is_prone else "No"), ("Yes" if is_hotspot else "No")
            
            st.markdown(f"""
                <div class='risk-indicator-container'>
                    <div class='indicator' title="Low-lying locations with a history of flooding, largely mitigated by drainage improvements.">{FLOOD_PRONE_ICON} Flood-Prone Area <span class='indicator-value' style='color: {prone_color};'>{prone_text}</span></div>
                    <div class='indicator' title="Not classified as low-lying but where flash floods have occurred, signaling localized flooding that needs attention.">{FLOOD_HOTSPOT_ICON} Flood Hotspot <span class='indicator-value' style='color: {hotspot_color};'>{hotspot_text}</span></div>
                </div>""", unsafe_allow_html=True)

            st.markdown("### Location Map")
            try:
                folium_static(create_flood_map(info, rcp85_depth), width=1300, height=400)
            except Exception as e:
                st.error("Error rendering map. Please try again later.")
        else:
            st.error(f"Postal code **{postal_code}** not found in database. Please check the code and try again.")

if __name__ == "__main__":

    main()


