import streamlit as st
import pandas as pd
import pydeck as pdk
import re
import time

# ------------------------
# Page Config & Enhanced CSS (Dark Volcano Theme + Responsive Design)
# ------------------------
st.set_page_config(page_title="Volcano Eruption Animation", layout="wide")

custom_css = """
<style>
  @import url('https://fonts.googleapis.com/css2?family=Roboto:wght@400;700&display=swap');

  /* Base styling for a volcanic theme */
  body, .stApp {
    background: #2e2e2e;
    font-family: 'Roboto', sans-serif;
    color: #e0e0e0;
    margin: 0;
    padding: 0;
  }

  /* Header styling with volcano eruption vibe */
  .header {
    text-align: center;
    padding: 2rem 1rem;
    background: linear-gradient(135deg, #8B0000, #FF4500);
    color: #fff;
    border-radius: 0 0 20px 20px;
    box-shadow: 0 8px 20px rgba(0, 0, 0, 0.3);
    margin-bottom: 2rem;
  }
  .header h1 {
    margin: 0;
    font-size: 2.8rem;
    letter-spacing: 1px;
    position: relative;
  }
  .header h1:before {
    content: "🌋 ";
    font-size: 1.2em;
    vertical-align: middle;
    margin-right: 0.3em;
  }

  /* Paragraph styling */
  p {
    line-height: 1.6;
    font-size: 1.1rem;
    color: #ccc;
  }

  /* Button styling */
  .stButton>button {
    background-color: #E74C3C;
    color: #fff;
    border: none;
    border-radius: 8px;
    padding: 0.75rem 1.5rem;
    font-size: 1rem;
    cursor: pointer;
    transition: background-color 0.3s ease, transform 0.2s ease;
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.2);
  }
  .stButton>button:hover {
    background-color: #C0392B;
    transform: translateY(-3px);
  }

  /* Responsive Slider styling */
  div[data-baseweb="slider"] {
    max-width: 30% !important;
    min-width: 30% !important;
    margin-left: 0 !important;
    color: #fff !important;
  }
  @media only screen and (max-width: 768px) {
    div[data-baseweb="slider"] {
      max-width: 100% !important;
      min-width: 100% !important;
    }
  }

  /* Data table styling */
  .custom-table {
    background: #424242;
    border-radius: 12px;
    padding: 1.5rem;
    margin: 1.5rem 0;
    box-shadow: 0 4px 20px rgba(0, 0, 0, 0.3);
    overflow-x: auto;
    transition: transform 0.3s ease;
  }
  .custom-table:hover {
    transform: translateY(-2px);
  }
  .custom-table table {
    width: 100%;
    border-collapse: collapse;
  }
  .custom-table th, .custom-table td {
    padding: 12px 16px;
    border: 1px solid #616161;
    text-align: left;
  }
  .custom-table th {
    background: #333;
    font-weight: 700;
    color: #fff;
  }
  .custom-table tr:nth-child(even) {
    background: #3a3a3a;
  }
  .custom-table td {
    color: #e0e0e0;
  }

  /* Hide data table on smartphones */
  @media only screen and (max-width: 768px) {
    .custom-table {
      display: none !important;
    }
  }

  /* Hide Volcano Data title on smartphones */
  @media only screen and (max-width: 768px) {
    .volcano-data-title {
      display: none !important;
    }
  }

  /* Info message styling */
  .stInfo {
    background-color: #37474f;
    color: #cfd8dc;
    border: 1px solid #546e7a;
    border-radius: 8px;
    padding: 1rem;
    margin: 1rem 0;
  }

  /* Tooltip styling for pydeck */
  .deck-tooltip {
    font-size: 0.9rem;
    line-height: 1.4;
    background: #424242;
    color: #fff;
    padding: 0.5rem;
    border-radius: 4px;
    border: 1px solid #E74C3C;
  }

  /* Responsive map styling */
  .stPydeckChart {
    height: 100px; /* Default map height for small screens */
  }
  @media only screen and (min-width: 768px) {
    .stPydeckChart {
      height: 600px; /* Larger map height for bigger screens */
    }
  }
</style>
"""
st.markdown(custom_css, unsafe_allow_html=True)
st.markdown('<div class="header"><h1>Volcano Eruption Animation (from 4360 BC to AD 2023)</h1></div>', unsafe_allow_html=True)

st.markdown(
    """
    <p style="text-align: center;">
    Animate volcano eruptions over time. Volcanoes are represented as grey circles, and those that are active (within a fade window) pulse in red.
    Adjust the simulation time frame and speed using the controls below.
    </p>
    """, unsafe_allow_html=True
)

# ------------------------
# Data Loading & Processing
# ------------------------
@st.cache_data
def load_data():
    try:
        df = pd.read_csv("volcano_data.csv")
    except Exception as e:
        st.error("Error reading CSV file: " + str(e))
        return pd.DataFrame()
    df.columns = df.columns.str.strip()
    return df

def extract_year(s):
    s = str(s)
    match = re.search(r"(-?\d{3,4})", s)
    return int(match.group(1)) if match else None

df = load_data()
required_columns = ["Volcano_Name", "Country", "Latitude", "Longitude", "Volcano_Type", "Last_Eruption"]
if not all(col in df.columns for col in required_columns):
    st.error(f"CSV file must contain columns: {required_columns}")
else:
    df["Eruption_Year"] = df["Last_Eruption"].apply(extract_year)

# ------------------------
# Simulation Setup
# ------------------------
pre_fade = 15   # Fade window before eruption
post_fade = 15  # Fade window after eruption

eruption_years = df["Eruption_Year"].dropna() if not df.empty else pd.Series()
if not eruption_years.empty:
    default_min = int(eruption_years.min()) - pre_fade
    default_max = int(eruption_years.max()) + post_fade
else:
    default_min, default_max = -4360, 2023

computed_min = min(default_min, -4360)
computed_max = 2023  # Force upper bound to 2023

simulation_range = st.slider(
    "Step 1 : Select Simulation Time Frame (years)",
    min_value=-4360,
    max_value=2023,
    value=(computed_min, computed_max),
    step=1,
    format="%d"
)

animation_speed = st.slider("Step 2 : Animation Speed (slide right for faster)", min_value=1, max_value=100, value=50, step=1)
animation_delay = 1.0 / animation_speed

# ------------------------
# Map Placeholder
# ------------------------
map_placeholder = st.empty()

tooltip = {
    "html": "<b>Name:</b> {Volcano_Name} <br/><b>Type:</b> {Volcano_Type} <br/><b>Last Eruption:</b> {Last_Eruption}",
    "style": {"backgroundColor": "black", "color": "white"}
}

def compute_color(row, sim_year, pre=5, post=5):
    eruption_year = row["Eruption_Year"]
    base_color = [200, 200, 200, 100]
    if pd.isna(eruption_year) or sim_year < eruption_year - pre or sim_year > eruption_year + post:
        return base_color
    if sim_year <= eruption_year:
        f = (sim_year - (eruption_year - pre)) / pre
    else:
        f = 1 - ((sim_year - eruption_year) / post)
    alpha = int(f * 180)
    return [255, 0, 0, alpha]

def update_map(sim_year):
    data_copy = df.copy()
    active_mask = (
        data_copy["Eruption_Year"].notna() &
        (sim_year >= data_copy["Eruption_Year"] - pre_fade) &
        (sim_year <= data_copy["Eruption_Year"] + post_fade)
    )
    active_df = data_copy[active_mask].copy()
    inactive_df = data_copy[~active_mask].copy()
    
    if not active_df.empty:
        active_df["color"] = active_df.apply(
            lambda row: compute_color(row, sim_year, pre=pre_fade, post=post_fade), axis=1
        )
    if not inactive_df.empty:
        inactive_df["color"] = [[200, 200, 200, 100]] * len(inactive_df)
    
    inactive_layer = pdk.Layer(
        "ScatterplotLayer",
        data=inactive_df,
        get_position='[Longitude, Latitude]',
        get_color="color",
        get_radius=180000,
        pickable=True,
        wrapLongitude=False
    )
    active_layer = pdk.Layer(
        "ScatterplotLayer",
        data=active_df,
        get_position='[Longitude, Latitude]',
        get_color="color",
        get_radius=350000,
        pickable=True,
        wrapLongitude=False
    )
    
    # ------------------------
    # NEW: Add Shock Wave Effect for Active Volcanoes
    # ------------------------
    shock_wave_layer = None
    if not active_df.empty:
        # Compute a dynamic ring effect based on current time
        current_time = time.time()
        cycle_duration = 1.5  # seconds for a full shock wave cycle
        t = (current_time % cycle_duration) / cycle_duration  # progress (0 to 1)
        base_radius = 350000  # same as active volcano radius
        max_extra = 150000    # maximum extra radius for the shock wave
        dynamic_radius = base_radius + t * max_extra
        shock_alpha = int((1 - t) * 200)  # fades out as it expands
        shock_color = [255, 255, 255, shock_alpha]  # white ring for a wow effect

        shock_wave_layer = pdk.Layer(
            "ScatterplotLayer",
            data=active_df,
            get_position='[Longitude, Latitude]',
            get_radius=dynamic_radius,
            stroked=True,
            filled=False,
            get_line_color=shock_color,
            lineWidthMinPixels=2,
            pickable=False,
            wrapLongitude=False
        )
    
    # Combine layers – insert the shock wave layer between inactive and active layers if available
    layers = [inactive_layer]
    if shock_wave_layer:
        layers.append(shock_wave_layer)
    layers.append(active_layer)
    
    view_state = pdk.ViewState(
        latitude=0,
        longitude=0,
        zoom=1.0,
        pitch=0
    )
    
    deck = pdk.Deck(
        layers=layers,
        initial_view_state=view_state,
        tooltip=tooltip,
        map_style="mapbox://styles/mapbox/dark-v10",
    )
    
    map_placeholder.pydeck_chart(deck, height=240)


# ------------------------
# Animation Execution with Legend on the Right
# ------------------------
if st.button("Start Animation"):
    # Create a legend container that appears on the right side during the animation
    legend_container = st.empty()
    legend_html = """
    <div style="position: fixed; bottom: 20px; right: 20px; background: rgba(46, 46, 46, 0.9); padding: 10px 15px; border-radius: 8px; z-index: 1000; box-shadow: 0px 4px 10px rgba(0,0,0,0.5);">
        <div style="display: flex; align-items: center; margin-bottom: 5px;">
            <div style="width: 15px; height: 15px; background: red; border-radius: 50%; margin-right: 8px;"></div>
            <span>Volcano Eruption</span>
        </div>
        <div style="display: flex; align-items: center;">
            <div style="width: 15px; height: 15px; background: grey; border-radius: 50%; margin-right: 8px;"></div>
            <span>Dormant Volcano</span>
        </div>
    </div>
    """
    legend_container.markdown(legend_html, unsafe_allow_html=True)
    
    total_years = simulation_range[1] - simulation_range[0] + 1
    progress_bar = st.progress(0)
    year_display = st.empty()
    
    for i, year in enumerate(range(simulation_range[0], simulation_range[1] + 1)):
        update_map(year)
        year_display.markdown(
            f"<h3 style='text-align: center;'>Simulation Year: {year}</h3>", unsafe_allow_html=True
        )
        progress_bar.progress((i + 1) / total_years)
        time.sleep(animation_delay)
    
    # Remove the legend after the animation ends
    legend_container.empty()
else:
    st.info("Press 'Start Animation' to run the simulation automatically.")

# ------------------------
# (Optional) Styled Data Table (Filtered by Selected Time Frame)
# ------------------------

# Replace st.subheader with st.markdown and a custom class so we can hide it in smartphone mode
st.markdown("<h2 class='volcano-data-title'>Volcano Data</h2>", unsafe_allow_html=True)
filtered_df = df[(df["Eruption_Year"] >= simulation_range[0]) & (df["Eruption_Year"] <= simulation_range[1])]
html_table = filtered_df.reset_index(drop=True).to_html(classes="custom-table", index=False)
st.markdown(html_table, unsafe_allow_html=True)
