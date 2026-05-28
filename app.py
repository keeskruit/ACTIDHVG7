import os
from datetime import datetime
import streamlit as st
import folium
from streamlit_folium import st_folium
import json

# Setup
st.set_page_config(
    page_title="Invader Mapper",
    page_icon="🌿",
    layout="wide"
)

# dark mode style
st.markdown("""
<style>

/* Main app background */
.stApp {
    background-color: #0E1117;
    color: white;
}

/* Sidebar */
[data-testid="stSidebar"] {
    background-color: #161A23;
}

/* Headers and text */
h1, h2, h3, h4, h5, h6, p, div, span, label {
    color: white !important;
}

/* Buttons */
.stButton>button {
    background-color: #262730;
    color: white;
    border-radius: 8px;
    border: 1px solid #444;
}

/* Input fields */
.stTextInput input,
.stTextArea textarea,
.stSelectbox div[data-baseweb="select"] {
    background-color: #262730 !important;
    color: white !important;
}

/* File uploader */
[data-testid="stFileUploader"] {
    background-color: #262730;
    border-radius: 10px;
    padding: 10px;
}

/* Expander */
.streamlit-expanderHeader {
    background-color: #262730;
    color: white;
}

/* Metric cards / containers */
[data-testid="stMetric"] {
    background-color: #262730;
}

/* Segmented control */
[data-baseweb="button-group"] {
    background-color: #262730;
}

</style>
""", unsafe_allow_html=True)

submissions_geojson = "data/uploads/submissions.geojson"
predicted_locations = "data/04_predicted_invasive_species_areas.geojson"
foto_folder = "data/uploads/fotos"

if "submission_status" not in st.session_state:
    st.session_state.submission_status = None

# Data Loading
@st.cache_data
def load_prediction_data():
    try:
        with open(predicted_locations, "r", encoding="utf-8") as f:
            data = json.load(f)
        return data
    except Exception:
        return None

@st.cache_data
def load_trails():
    try:
        with open("data/04_trails_Groenlo.geojson", "r", encoding="utf-8") as f:
            data = json.load(f)
        return data
    except Exception:
        return None

def save_submission_to_geojson(
    species: str,
    latitude: float,
    longitude: float,
    notes: str,
    image_path: str
):
    feature = {
        "type": "Feature",
        "geometry": {
            "type": "Point",
            "coordinates": [longitude, latitude]
        },
        "properties": {
            "species": species,
            "field_notes": notes,
            "datetime": datetime.utcnow().isoformat(),
            "image_path": image_path,
            "status": "Pending"
        }
    }

    # Ensure folder exists
    os.makedirs(os.path.dirname(submissions_geojson), exist_ok=True)
    # Load existing file or create new structure
    if os.path.exists(submissions_geojson):
        with open(submissions_geojson, "r", encoding="utf-8") as f:
            data = json.load(f)
    else:
        data = {"type": "FeatureCollection", "features": []}
    data["features"].append(feature)
    # Write back
    with open(submissions_geojson, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)

@st.cache_data
def load_submissions():
    try:
        with open("data/uploads/submissions.geojson", "r", encoding="utf-8") as f:
            data = json.load(f)
        return data
    except Exception:
        return None

dashboard = st.segmented_control(
    "Navigation",
    options=["Citizen Dashboard", "Municipality Dashboard"],
    default="Citizen Dashboard"
)

# Title and logo

title_col, logo_col = st.columns([6, 1])
with title_col:
    st.header("Invader Mapper")

with logo_col:
    st.image("media/App_logo.png", width=80)

# -------------------------------------
# Citizen Dashboard
# -------------------------------------

if dashboard == "Citizen Dashboard":
    left_col, map_col, right_col = st.columns([1, 5, 1])
    species_info = {
        "Japanese Knotweed": {
            "image": "media/japanese_knotweed.jpg",
            "description": "Japanese Knotweed is native to East Asia in Korea, Japan and China, between 1820-1845 it was"
                           " introduced to Europe as an ornamental plant. The plant can get 2 to 4 meters high, and the "
                           "stems look a little bit like a bamboo stem. The leaves are around 15 cm long and oval shaped,"
                           " the flowers are small and white, just like in the picture, and the plant flowers in August "
                           "and September. The roots can extend up to 3 meters deep, which makes it very hard to exterminate."
                           " The plant grows in patches, often next to roads or waterways."
        },
        "Giant Hogweed": {
            "image": "media/giant_hogweed.jpg",
            "description": "The Giant Hogweed is native to Western Caucasus and was introduced in Europe in the 19th century"
                           " as an ornamental plant. The plants size ranges from 2 to 5 meters, and in perfect conditions"
                           " can reach heights of up to 6 meters! The flowers are small and white as in the images and they"
                           " flower in June and July. The height and the big leaves deprive native plant species of the "
                           "sunlight they need to grow. Be aware, if you touch this plant, it can severely burn you!"
        },
        "Himalayan Balsam": {
            "image": "media/himalayan_balsam.jpg",
            "description": "Himalayan Balsem is native to Northern India and was introduced to Europe around 1850 as an "
                           "ornamental plant. It can grow up to 2,5 meters, it has 2,5 to 4,5 centimeter long purple flowers, "
                           "like in the image, and they bloom between June and October. It is also well known for its exploding"
                           " seed pods, which form after flowering."
        }
    }

    # Species Selection
    if "selected_species" not in st.session_state:
        st.session_state.selected_species = "Japanese Knotweed"
    if "active_species_popup" not in st.session_state:
        st.session_state.active_species_popup = None
    if "clicked_location" not in st.session_state:
        st.session_state.clicked_location = None

    if st.session_state.active_species_popup:
        popup_species = st.session_state.active_species_popup
        @st.dialog(popup_species)
        def species_popup():
            st.image(species_info[popup_species]["image"], use_container_width=True)
            st.markdown(species_info[popup_species]["description"])
            if st.button("Close"):
                st.session_state.active_species_popup = None
                st.rerun()
        species_popup()


    with left_col:
        st.subheader("Targeted Invasive Species")
        for species_name in species_info.keys():
            if st.button(species_name, use_container_width=True):
                st.session_state.selected_species = species_name
                st.session_state.active_species_popup = species_name
            st.image(
                species_info[species_name]["image"],
                use_container_width=True
            )

    # Map Display
    with map_col:
        st.subheader("Locate the species on the map below")
        trails_gdf = load_trails()
        map_center = [52.052, 6.718]
        m = folium.Map(
            location=map_center,
            zoom_start=13,
            tiles="OpenStreetMap"
        )
        # add trails
        if trails_gdf is not None:
            folium.GeoJson(
                trails_gdf,
                name="Trails",
                style_function=lambda feature: {
                    "color": "#7f6000",
                    "weight": 3,
                    "opacity": 0.8
                },
                tooltip=folium.GeoJsonTooltip(
                    fields=["id"],
                    aliases=["Trail ID:"]
                )
            ).add_to(m)
        if st.session_state.clicked_location is not None:
            folium.Marker(
                location=[
                    st.session_state.clicked_location["lat"],
                    st.session_state.clicked_location["lng"]
                ],
                popup="Selected observation location",
                tooltip="Selected location",
                icon=folium.Icon(
                    color="green",
                    icon="ok-sign"
                )
            ).add_to(m)

        map_data = st_folium(
            m,
            width=900,
            height=600
        )
        # save clicked point
        if map_data and map_data.get("last_clicked"):
            st.session_state.clicked_location = map_data["last_clicked"]
            st.rerun()

        clicked_location = st.session_state.clicked_location

        if clicked_location:
            st.success(
                f"Selected location: "
                f"{clicked_location['lat']:.6f}, "
                f"{clicked_location['lng']:.6f}"
            )

    # Leaderboard
    with right_col:
        st.subheader("Leaderboard")                 # dummy data
        st.markdown("""
        ### Top Contributors

        🥇 Hans — 32 observations  
        🥈 Marie-Claire — 28 observations  
        🥉 Klaas — 21 observations  
        4. Fleur — 15 observations  
        5. Jan-Peter — 11 observations  
        """)

    # Submission form
    st.divider()
    st.subheader("Submit Observation")
    live_photo = st.camera_input("Take a photo of the invasive species")
    uploaded_photo = st.file_uploader("Or upload existing photo", type=["jpg", "jpeg", "png"])
    photo = live_photo if live_photo is not None else uploaded_photo
    notes = st.text_area(
        "Field Notes",
        placeholder="Optional notes about the observation..."
    )
    if clicked_location:
        latitude = clicked_location["lat"]
        longitude = clicked_location["lng"]
        st.write(f"Latitude: {latitude:.6f}")
        st.write(f"Longitude: {longitude:.6f}")
    else:
        latitude = None
        longitude = None
        st.warning("Click on the map to select a location.")

    if st.button("Submit Observation"):
        if photo is None:
            st.error("Please upload a photo.")
        elif clicked_location is None:
            st.error("Please select a location on the map.")
        else:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"{timestamp}_{photo.name}"
            save_path = os.path.join(
                foto_folder,
                filename
            )
            os.makedirs(foto_folder, exist_ok=True)
            with open(save_path, "wb") as f:
                f.write(photo.read())
            save_submission_to_geojson(
                species=st.session_state.selected_species,
                latitude=latitude,
                longitude=longitude,
                notes=notes,
                image_path=save_path
            )
            load_submissions.clear()
            st.success("Observation submitted successfully!")
            st.rerun()

# -------------------------------------
# Municipality Dashboard
# -------------------------------------

elif dashboard == "Municipality Dashboard":
    st.subheader("Municipality Dashboard")
    submissions = load_submissions()
    prediction_data = load_prediction_data()
    if (submissions is None or "features" not in submissions or len(submissions["features"]) == 0):
        st.info("No submissions yet.")
        st.stop()

    features = submissions["features"]
    # selected observation state
    if "selected_observation" not in st.session_state:
        st.session_state.selected_observation = 0

    list_col, detail_col = st.columns([1, 2])

    # Observation list
    with list_col:
        st.subheader("Observations")
        for idx, feature in enumerate(features):
            props = feature["properties"]
            species = props.get("species", "Unknown")
            status = props.get("status", "pending")
            with st.container(border=True):
                if st.button(
                    f"{species} ({status})",
                    key=f"select_{idx}",
                    use_container_width=True
                ):
                    st.session_state.selected_observation = idx
                accept_col, reject_col = st.columns(2)
                # Action buttons
                with accept_col:
                    if st.button(
                        "✅ Accept",
                        key=f"accept_{idx}",
                        use_container_width=True
                    ):
                        submissions["features"][idx]["properties"]["status"] = "verified"
                        with open(submissions_geojson, "w", encoding="utf-8") as f:
                            json.dump(submissions, f, indent=2)
                        load_submissions.clear()
                        st.success("Observation verified")
                        st.rerun()
                with reject_col:
                    if st.button(
                        "❌ Reject",
                        key=f"reject_{idx}",
                        use_container_width=True
                    ):
                        submissions["features"][idx]["properties"]["status"] = "rejected"
                        with open(submissions_geojson, "w", encoding="utf-8") as f:
                            json.dump(submissions, f, indent=2)
                        load_submissions.clear()
                        st.warning("Observation rejected")
                        st.rerun()

    # Submission details
    with detail_col:
        selected_idx = st.session_state.selected_observation
        selected_feature = features[selected_idx]
        props = selected_feature["properties"]
        coords = selected_feature["geometry"]["coordinates"]
        lon = coords[0]
        lat = coords[1]
        st.subheader("Observation Details")
        m = folium.Map(
            location=[lat, lon],
            zoom_start=16
        )
        if prediction_data is not None:
            folium.GeoJson(
                prediction_data,
                name="Predictions",
                style_function=lambda feature: {
                    "fillColor": "red",
                    "color": "red",
                    "weight": 1,
                    "fillOpacity": 0.5
                }
            ).add_to(m)

        folium.Marker(
            location=[lat, lon],
            popup=props.get("species", "Unknown"),
            icon=folium.Icon(
                color="red",
                icon="info-sign"
            )
        ).add_to(m)

        st_folium(m, width=900, height=400)
        st.markdown(f"### {props.get('species', 'Unknown')}")
        st.write("**Status:**", props.get("status", "pending"))
        st.write("**Datetime:**", props.get("datetime", ""))
        st.write("**Notes:**", props.get("field_notes", ""))
        image_path = props.get("image_path", "")
        if image_path and os.path.exists(image_path):
            st.image(image_path, use_container_width=True)
        else:
            st.info("No image available")

st.markdown(
    """
    <hr style="margin-top: 2rem; margin-bottom: 0.5rem;">
    <div style="text-align: center; font-size: 12px; opacity: 0.7;">
        Image credits: Wikimedia Commons
    </div>
    """,
    unsafe_allow_html=True
)

left, center, right = st.columns([1, 1, 1])
with center:
    st.image("media/Atlas_logo.png", width=500)
