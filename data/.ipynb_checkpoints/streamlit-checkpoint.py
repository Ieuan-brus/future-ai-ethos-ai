import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(
    page_title="RQ1 – Gender patterns by HSE region",
    layout="wide"
)

# map data
# Load the GeoJSON file
geojson_path = "map_data/hse_regions.geojson"



st.title("RQ1 – Gender Patterns of Health Graduates by HSE Region")

@st.cache_data
def load_data(path: str):
    df = pd.read_csv(path)
    df["Graduation Year"] = df["Graduation Year"].astype(int)
    return df

DATA_PATH = "cleaned_gender_pivot.csv"
df = load_data(DATA_PATH)

# ---- SIDEBAR FILTERS ----
st.sidebar.header("Filters")

years = sorted(df["Graduation Year"].unique())
min_year, max_year = int(min(years)), int(max(years))

year_range = st.sidebar.slider(
    "Graduation Year range",
    min_value=min_year,
    max_value=max_year,
    value=(min_year, max_year),
    step=1,
)

field_options = ["All Fields"] + sorted(df["Field of Study"].unique())
selected_field = st.sidebar.selectbox("Field of Study", field_options)

region_options = ["All Regions"] + sorted(df["HSE Health Regions"].unique())
selected_region = st.sidebar.selectbox("HSE Health Region", region_options)

# ---- APPLY FILTERS ----
filtered = df[
    (df["Graduation Year"] >= year_range[0])
    & (df["Graduation Year"] <= year_range[1])
]

if selected_field != "All Fields":
    filtered = filtered[filtered["Field of Study"] == selected_field]

if selected_region != "All Regions":
    filtered = filtered[filtered["HSE Health Regions"] == selected_region]

if filtered.empty:
    st.warning("No data for the selected filter combination.")
    st.stop()

# ---- COMMON COLOUR SCHEME ----
FEMALE_COLOR = "#e377c2"  # pink/magenta
MALE_COLOR = "#1f77b4"    # blue

# ---- PREP DATA FOR CHARTS ----

# 1. Grouped bar chart data
grouped = (
    filtered
    .groupby("HSE Health Regions", as_index=False)[["Female", "Male"]]
    .sum()
)

# 2. Donut chart data (overall gender share for filtered subset)
total_female = filtered["Female"].sum()
total_male = filtered["Male"].sum()

gender_totals = pd.DataFrame({
    "Gender": ["Female", "Male"],
    "Count": [total_female, total_male],
})

# 3. Box plot data (long format)
long_df = filtered.melt(
    id_vars=["HSE Health Regions", "Graduation Year", "Field of Study"],
    value_vars=["Female", "Male"],
    var_name="Gender",
    value_name="Graduate Count",
)

# ---- TABS ----
tab1, tab2, tab3, tab4 = st.tabs([
    "Grouped Bar Chart",
    "Gender Donut Chart",
    "Outlier Box Plot",
    "choropleth chart
])

# ---- TAB 1: GROUPED BAR CHART ----
with tab1:
    st.subheader("1. Graduate counts by gender and HSE health region")

    fig_bar = px.bar(
        grouped,
        x="HSE Health Regions",
        y=["Female", "Male"],
        barmode="group",
        labels={
            "value": "Number of graduates",
            "HSE Health Regions": "HSE Health Region",
            "variable": "Gender",
        },
    )

    # Set colours for Female and Male traces
    for trace in fig_bar.data:
        if trace.name == "Female":
            trace.marker.color = FEMALE_COLOR
        elif trace.name == "Male":
            trace.marker.color = MALE_COLOR

    fig_bar.update_layout(
        xaxis_title="HSE Health Region",
        yaxis_title="Number of graduates",
        legend_title_text="Gender",
    )

    st.plotly_chart(fig_bar, use_container_width=True)

# ---- TAB 2: DONUT CHART ----
with tab2:
    st.subheader("2. Gender share of graduates (filtered subset)")

    fig_donut = px.pie(
        gender_totals,
        values="Count",
        names="Gender",
        hole=0.4,
        color="Gender",
        color_discrete_map={
            "Female": FEMALE_COLOR,
            "Male": MALE_COLOR,
        },
    )

    fig_donut.update_traces(
        textposition="inside",
        textinfo="label+percent+value"
    )

    fig_donut.update_layout(
        showlegend=True
    )

    st.plotly_chart(fig_donut, use_container_width=True)

# ---- TAB 3: OUTLIER BOX PLOT ----
with tab3:
    st.subheader("3. Outliers in graduate counts by gender and region")

    fig_box = px.box(
        long_df,
        x="HSE Health Regions",
        y="Graduate Count",
        color="Gender",
        points="outliers",
        color_discrete_map={
            "Female": FEMALE_COLOR,
            "Male": MALE_COLOR,
        },
        labels={
            "HSE Health Regions": "HSE Health Region",
            "Graduate Count": "Graduate count",
            "Gender": "Gender",
        },
    )

    fig_box.update_layout(
        xaxis_title="HSE Health Region",
        yaxis_title="Graduate count",
        legend_title_text="Gender",
    )

    st.plotly_chart(fig_box, use_container_width=True)

# --------- tab 4 choropleth map ---- 
with tab4:
    try:
        gdf = gpd.read_file(geojson_path)

        # Create folium map
        m = folium.Map(location=[53.4, -7.6], zoom_start=7, tiles="cartodbpositron")

        folium.GeoJson(
            gdf,
            name="HSE Regions",
            tooltip=GeoJsonTooltip(fields=["county", "hse_region"]),
            style_function=lambda feature: {
                'fillColor': '#66c2a5',
                'color': 'black',
                'weight': 1,
                'fillOpacity': 0.6
            },
            highlight_function=lambda feature: {
                'weight': 3,
                'color': 'blue',
                'fillOpacity': 0.9
            }
        ).add_to(m)

        folium.LayerControl().add_to(m)

        # Show map in Streamlit
        st_data = st_folium(m, width=1000, height=700)

        except Exception as e:
            st.error(f"❌ Error loading or rendering map:\n{e}")