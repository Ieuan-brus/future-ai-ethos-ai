import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(
    page_title="Health Graduate Gender Inequality Dashboard",
    layout="wide"
)

st.title("Health Graduate Gender Inequality Dashboard")

# ---- TOP-LEVEL TABS FOR RQs ----
rq1_tab, rq2_tab, rq3_tab = st.tabs(
    ["RQ1: Regional gender patterns", "RQ2", "RQ3"]
)

# ================================
# RQ1: CURRENT DASHBOARD (YOUR CSV)
# ================================
@st.cache_data
def load_rq1_data(path: str):
    df = pd.read_csv(path)
    df["Graduation Year"] = df["Graduation Year"].astype(int)
    return df

# Colours reused in all charts
FEMALE_COLOR = "#e377c2"  # pink-ish for Female
MALE_COLOR = "#1f77b4"    # blue for Male

with rq1_tab:
    st.header("RQ1 – Gender patterns of health graduates by HSE region")

    DATA_PATH_RQ1 = "cleaned_gender_pivot.csv"
    df = load_rq1_data(DATA_PATH_RQ1)

    # ---- SIDEBAR FILTERS (RQ1 ONLY) ----
    st.sidebar.header("RQ1 Filters")

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
    selected_field = st.sidebar.selectbox("Field of Study", field_options, key="rq1_field")

    region_options = ["All Regions"] + sorted(df["HSE Health Regions"].unique())
    selected_region = st.sidebar.selectbox("HSE Health Region", region_options, key="rq1_region")

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
        st.warning("No data for the selected RQ1 filter combination.")
        st.stop()

    # ---- PREP DATA FOR CHARTS ----

    # 1. Grouped bar chart data
    grouped = (
        filtered
        .groupby("HSE Health Regions", as_index=False)[["Female", "Male"]]
        .sum()
    )

    # 2. Donut chart data
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

    # ---- INNER TABS FOR THE THREE CHARTS ----
    tab1, tab2, tab3 = st.tabs([
        "Grouped Bar Chart",
        "Gender Donut Chart",
        "Outlier Box Plot"
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

# ================================
# RQ2: PLACEHOLDER / FUTURE DATASET
# ================================
with rq2_tab:
    st.header("RQ2 – (placeholder)")
    st.info(
        "This tab is ready for a different dataset and question.\n\n"
        "You can load a separate CSV here and define its own filters and charts."
    )
    # Example scaffold:
    # rq2_file = st.file_uploader("Upload RQ2 dataset", type=["csv"])
    # if rq2_file is not None:
    #     rq2_df = pd.read_csv(rq2_file)
    #     st.write(rq2_df.head())

# ================================
# RQ3: PLACEHOLDER / FUTURE DATASET
# ================================
with rq3_tab:
    st.header("RQ3 – (placeholder)")
    st.info(
        "Another slot for a separate research question and dataset.\n\n"
        "You can copy the RQ1 pattern (filters + chart tabs) and adapt it here."
    )