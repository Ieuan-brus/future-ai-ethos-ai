import streamlit as st
import pandas as pd
import plotly.express as px
from pathlib import Path

# imports for map
import geopandas as gpd
import folium
from folium.features import GeoJsonTooltip
from streamlit.components.v1 import html


st.set_page_config(
    page_title="Health Graduate Gender Inequality Dashboard",
    layout="wide"
)

BASE_DIR = Path(__file__).resolve().parent

st.title("Health Graduate Gender Inequality Dashboard")

# ---- TOP-LEVEL TABS FOR RQs ----
rq1_tab, rq2_tab, rq3_tab = st.tabs(
    ["RQ1", "RQ2", "RQ3"]
)

# ================================
# RQ1: CURRENT DASHBOARD (YOUR CSV)
# ================================
@st.cache_data
def load_rq1_data(path: Path):
    df = pd.read_csv(path)
    df["Graduation Year"] = df["Graduation Year"].astype(int)
    return df

@st.cache_data
def load_rq2_data(path: Path):
    df = pd.read_csv(path)
    df["Graduation Year"] = df["Graduation Year"].astype(int)
    return df

@st.cache_data
def load_rq3_data(path: Path):
    df = pd.read_csv(path)
    df["Graduation Year"] = df["Graduation Year"].astype(int)
    df["Years since Graduation"] = df["Years since Graduation"].astype(int)
    return df

@st.cache_data
def load_hse_shapes(shapefile_path: Path):
    """Load county shapefile (level 2) and dissolve into HSE regions using a mapping.
    Dublin is split into north/south-west/south-east quadrants; Wicklow split east/west.
    """
    county_to_region = {
        # Dublin split across regions in reality; base mapping overridden by quadrant split
        "Dublin": "HSE Dublin and North East",
        # Midlands
        "Kildare": "HSE Dublin and Midlands",
        "Laois": "HSE Dublin and Midlands",
        "Offaly": "HSE Dublin and Midlands",
        "Longford": "HSE Dublin and Midlands",
        "Westmeath": "HSE Dublin and Midlands",
        # North East
        "Louth": "HSE Dublin and North East",
        "Meath": "HSE Dublin and North East",
        "Monaghan": "HSE Dublin and North East",
        "Cavan": "HSE Dublin and North East",
        # South East (assign Wicklow + Tipperary fully here for mapping simplicity)
        "Carlow": "HSE Dublin and South East",
        "Kilkenny": "HSE Dublin and South East",
        "Waterford": "HSE Dublin and South East",
        "Wexford": "HSE Dublin and South East",
        "Wicklow": "HSE Dublin and South East",
        "Tipperary": "HSE Dublin and South East",
        # Mid West
        "Clare": "HSE Midwest",
        "Limerick": "HSE Midwest",
        # South West
        "Cork": "HSE South West",
        "Cork City": "HSE South West",
        "Kerry": "HSE South West",
        # City-only shapes
        "Dublin City": "HSE Dublin and South East",
        "Fingal": "HSE Dublin and South East",
        "South Dublin": "HSE Dublin and South East",
        "Dun Laoghaire-Rathdown": "HSE Dublin and South East",
        # West & North West
        "Galway": "HSE West and North West",
        "Mayo": "HSE West and North West",
        "Roscommon": "HSE West and North West",
        "Sligo": "HSE West and North West",
        "Leitrim": "HSE West and North West",
        "Donegal": "HSE West and North West",
    }

    counties = gpd.read_file(shapefile_path)
    counties["county_name"] = counties["NAME_1"]

    # Precompute bounds for Dublin and Wicklow to split quadrants/halves
    dublin_geom = counties[counties["county_name"] == "Dublin"].geometry
    wicklow_geom = counties[counties["county_name"] == "Wicklow"].geometry
    dublin_bounds = dublin_geom.unary_union.bounds if not dublin_geom.empty else None
    wicklow_bounds = wicklow_geom.unary_union.bounds if not wicklow_geom.empty else None

    def region_for_row(row):
        county = row["county_name"]
        geom = row.geometry
        if county == "Dublin" and dublin_bounds:
            minx, miny, maxx, maxy = dublin_bounds
            midx = (minx + maxx) / 2
            midy = (miny + maxy) / 2
            cx, cy = geom.centroid.x, geom.centroid.y
            if cy >= midy:
                return "HSE Dublin and North East"  # north half
            # south half: split east (SE) vs west (Midlands) by midpoint
            if cx >= midx:
                return "HSE Dublin and South East"
            return "HSE Dublin and Midlands"
        if county == "Wicklow" and wicklow_bounds:
            minx, _, maxx, _ = wicklow_bounds
            midx = (minx + maxx) / 2
            cx = geom.centroid.x
            if cx < midx:
                return "HSE Dublin and Midlands"   # west half
            return "HSE Dublin and South East"     # east half
        return county_to_region.get(county)

    counties["HSE Health Regions"] = counties.apply(region_for_row, axis=1)
    counties = counties.dropna(subset=["HSE Health Regions"])

    # Dissolve counties into HSE regions
    regions = counties.dissolve(by="HSE Health Regions").reset_index()
    return regions

# Colours reused in all charts
FEMALE_COLOR = "#e377c2"  # pink-ish for Female
MALE_COLOR = "#1f77b4"    # blue for Male

with rq1_tab:
    st.header("RQ1 – Gender patterns of health graduates by HSE region")
    st.markdown(
        "**Research Question:** What are the regional patterns of health graduate employment by "
        "gender in Ireland, and which HSE regions show the greatest gender disparities? "
        "_Focus: Compare male vs. female distribution across 6 HSE regions for nursing, "
        "medicine, and social care graduates._"
    )
    st.text_area("RQ1 Findings / Notes", value="", height=120, key="rq1_findings")

    DATA_PATH_RQ1 = BASE_DIR / "cleaned" / "rq1" / "cleaned_gender_pivot.csv"
    df = load_rq1_data(DATA_PATH_RQ1)

    # ---- SIDEBAR FILTERS (RQ1 ONLY) ----
    with st.sidebar:
        with st.expander("RQ1 Filters", expanded=True):
            years = sorted(df["Graduation Year"].unique())
            min_year, max_year = int(min(years)), int(max(years))

            year_range = st.slider(
                "Graduation Year range",
                min_value=min_year,
                max_value=max_year,
                value=(min_year, max_year),
                step=1,
            )

            field_options = ["All Fields"] + sorted(df["Field of Study"].unique())
            selected_field = st.selectbox("Field of Study", field_options, key="rq1_field")

            region_options = ["All Regions"] + sorted(df["HSE Health Regions"].unique())
            selected_region = st.selectbox("HSE Health Region", region_options, key="rq1_region")

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

    # 4. Gender ratio over time (aggregated per year/region)
    ratio_df = (
        filtered
        .groupby(["Graduation Year", "HSE Health Regions"], as_index=False)[["Female", "Male"]]
        .sum()
    )
    ratio_df["Gender Ratio (F/M)"] = ratio_df.apply(
        lambda row: row["Female"] / row["Male"] if row["Male"] > 0 else None,
        axis=1,
    )
    ratio_df = ratio_df.dropna(subset=["Gender Ratio (F/M)"])

    # 5. Map data prep: aggregate by region for selected filters
    region_agg = (
        filtered
        .groupby("HSE Health Regions", as_index=False)[["Female", "Male", "Total Graduates"]]
        .sum()
    )
    region_agg["Gender Ratio (F/M)"] = region_agg.apply(
        lambda row: row["Female"] / row["Male"] if row["Male"] > 0 else None,
        axis=1,
    )

    # ---- INNER TABS FOR THE CHARTS ----
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "Grouped Bar Chart",
        "Gender Donut Chart",
        "Outlier Box Plot",
        "Gender Ratio Over Time",
        "HSE Region Map",
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

    # ---- TAB 4: GENDER RATIO OVER TIME ----
    with tab4:
        st.subheader("4. Female-to-male ratio over time by HSE health region")

        if ratio_df.empty:
            st.info("No data available to compute ratios for the selected filters.")
        else:
            fig_ratio = px.line(
                ratio_df,
                x="Graduation Year",
                y="Gender Ratio (F/M)",
                color="HSE Health Regions",
                markers=True,
                labels={
                    "Gender Ratio (F/M)": "Female / Male ratio",
                    "HSE Health Regions": "HSE Health Region",
                    "Graduation Year": "Graduation Year",
                },
            )

            fig_ratio.update_layout(
                yaxis_title="Female / Male ratio",
                legend_title_text="HSE Health Region",
            )

            st.plotly_chart(fig_ratio, use_container_width=True)

    # ---- TAB 5: CHOROPLETH MAP ----
    with tab5:
        st.subheader("5. HSE health regions map")

        map_metric = st.radio(
            "Select map metric",
            ["Female", "Male", "Gender Ratio (F/M)"],
            horizontal=True,
            key="map_metric_rq1",
        )

        shapefile_path = BASE_DIR / "map_data" / "gadm41_IRL_shp" / "gadm41_IRL_2.shp"

        try:
            regions_gdf = load_hse_shapes(shapefile_path)
        except Exception as e:
            st.error(f"Could not load region shapes: {e}")
            st.stop()

        metric_df = region_agg[["HSE Health Regions", map_metric]].dropna(subset=[map_metric])

        if metric_df.empty:
            st.info("No data available to display on the map for the selected filters/metric.")
        else:
            regions_gdf = regions_gdf.merge(metric_df, on="HSE Health Regions", how="left")

            # Build folium map
            m = folium.Map(location=[53.4, -7.6], zoom_start=7, tiles="cartodbpositron")

            # Choropleth
            folium.Choropleth(
                geo_data=regions_gdf.__geo_interface__,
                data=regions_gdf,
                columns=["HSE Health Regions", map_metric],
                key_on="feature.properties.HSE Health Regions",
                fill_color="YlGnBu",
                fill_opacity=0.7,
                line_opacity=0.6,
                nan_fill_opacity=0.15,
                legend_name=f"{map_metric}",
            ).add_to(m)

            folium.GeoJson(
                regions_gdf,
                name="HSE Regions",
                tooltip=GeoJsonTooltip(
                    fields=["HSE Health Regions", map_metric],
                    aliases=["Region", map_metric],
                    localize=True,
                ),
            ).add_to(m)

            folium.LayerControl().add_to(m)

            # Render folium map via HTML to avoid component serialization issues
            m.get_root().render()
            html(m._repr_html_(), height=700)

# ================================
# RQ2: PLACEHOLDER / FUTURE DATASET
# ================================
with rq2_tab:
    st.header("RQ2 – Occupational segregation and seniority")
    st.markdown(
        "**Research Question:** How do occupational outcomes differ between male and female health "
        "graduates, and is there evidence of vertical segregation (e.g., men in senior roles)? "
        "_Focus: Analyse whether male graduates disproportionately occupy managerial/senior "
        "positions despite being a minority in healthcare fields._"
    )
    st.markdown(
        "Use the filters on the left to set the graduation years, fields of study, and occupational "
        "groups you want to compare. All charts update based on the current filters, so tighten the "
        "selection to focus on specific roles or fields when exploring differences."
    )
    st.text_area("RQ2 Findings / Notes", value="", height=120, key="rq2_findings")

    DATA_PATH_RQ2 = BASE_DIR / "cleaned" / "rq2" / "cleaned_graduate_gender_ocupations.csv"
    rq2_df = load_rq2_data(DATA_PATH_RQ2)

    # ---- RQ2 SIDEBAR FILTERS ----
    with st.sidebar:
        with st.expander("RQ2 Filters", expanded=True):
            years_rq2 = sorted(rq2_df["Graduation Year"].unique())
            min_year_rq2, max_year_rq2 = int(min(years_rq2)), int(max(years_rq2))
            year_range_rq2 = st.slider(
                "Graduation Year range (RQ2)",
                min_value=min_year_rq2,
                max_value=max_year_rq2,
                value=(min_year_rq2, max_year_rq2),
                step=1,
            )

            field_options_rq2 = list(rq2_df["Field of Study"].unique())
            selected_fields_rq2 = st.multiselect(
                "Field of Study (RQ2)",
                options=field_options_rq2,
                default=field_options_rq2,
            )

            occupation_options = list(rq2_df["Occupations"].unique())
            st.caption("Select occupational groups to include (all on by default).")
            selected_occupations = []
            for occ in occupation_options:
                if st.checkbox(
                    occ,
                    value=st.session_state.get(f"rq2_occ_{occ}", True),
                    key=f"rq2_occ_{occ}",
                ):
                    selected_occupations.append(occ)

    # ---- APPLY FILTERS ----
    rq2_filtered = rq2_df[
        (rq2_df["Graduation Year"] >= year_range_rq2[0])
        & (rq2_df["Graduation Year"] <= year_range_rq2[1])
        & (rq2_df["Field of Study"].isin(selected_fields_rq2))
        & (rq2_df["Occupations"].isin(selected_occupations))
    ]

    if rq2_filtered.empty:
        st.warning("No data for the selected RQ2 filter combination.")
        st.stop()

    # ---- DATA PREP ----
    # Total graduates by gender
    gender_totals_rq2 = (
        rq2_filtered
        .groupby("Gender", as_index=False)["VALUE"]
        .sum()
        .rename(columns={"VALUE": "Total Graduates"})
    )
    # Overall female/male ratio for legend context
    total_female = float(gender_totals_rq2.loc[gender_totals_rq2["Gender"] == "Female", "Total Graduates"].sum())
    total_male = float(gender_totals_rq2.loc[gender_totals_rq2["Gender"] == "Male", "Total Graduates"].sum())
    overall_ratio = (total_female / total_male) if total_male > 0 else None
    ratio_label = f" (F/M: {overall_ratio:.2f})" if overall_ratio is not None else ""

    # Manager share by gender
    manager_label = "Managers, directors and senior officials"
    managers_df = rq2_filtered[rq2_filtered["Occupations"] == manager_label]
    manager_counts = managers_df.groupby("Gender", as_index=False)["VALUE"].sum().rename(columns={"VALUE": "Manager Count"})
    manager_totals = rq2_filtered.groupby("Gender", as_index=False)["VALUE"].sum().rename(columns={"VALUE": "Total"})
    manager_share = manager_totals.merge(manager_counts, on="Gender", how="left").fillna({"Manager Count": 0})
    manager_share["Manager Share (%)"] = manager_share.apply(
        lambda r: (r["Manager Count"] / r["Total"]) * 100 if r["Total"] > 0 else 0,
        axis=1,
    )

    # Occupation distribution by gender (% within gender)
    occ_dist = (
        rq2_filtered
        .groupby(["Gender", "Occupations"], as_index=False)["VALUE"]
        .sum()
    )
    occ_dist["Gender Total"] = occ_dist.groupby("Gender")["VALUE"].transform("sum")
    occ_dist["Share (%)"] = occ_dist.apply(
        lambda r: (r["VALUE"] / r["Gender Total"]) * 100 if r["Gender Total"] > 0 else 0,
        axis=1,
    )

    # Facet: manager share by gender per field
    manager_by_field = (
        rq2_filtered[rq2_filtered["Occupations"] == manager_label]
        .groupby(["Field of Study", "Gender"], as_index=False)["VALUE"]
        .sum()
        .rename(columns={"VALUE": "Manager Count"})
    )
    total_by_field_gender = (
        rq2_filtered.groupby(["Field of Study", "Gender"], as_index=False)["VALUE"]
        .sum()
        .rename(columns={"VALUE": "Total"})
    )
    field_share = total_by_field_gender.merge(manager_by_field, on=["Field of Study", "Gender"], how="left").fillna({"Manager Count": 0})
    field_share["Manager Share (%)"] = field_share.apply(
        lambda r: (r["Manager Count"] / r["Total"]) * 100 if r["Total"] > 0 else 0,
        axis=1,
    )

    st.divider()
    st.subheader("RQ2 Charts")

    tab_a, tab_b, tab_c, tab_d, tab_e = st.tabs([
        "Total by Gender",
        "Manager Share",
        "Occupation Distribution",
        "Manager Share by Field",
        "Trends Over Time",
    ])

    with tab_a:
        st.caption("This chart reflects the total male and female graduates after applying all current filters; hover to see exact counts.")
        st.markdown("**1. Total graduates by gender**")
        fig_total = px.bar(
            gender_totals_rq2,
            x="Gender",
            y="Total Graduates",
            color="Gender",
            color_discrete_map={"Female": FEMALE_COLOR, "Male": MALE_COLOR},
        )
        # Update legend names to include overall ratio context
        for trace in fig_total.data:
            if trace.name == "Female":
                trace.name = f"Female{ratio_label}"
            trace.hovertemplate = "Gender: %{x}<br>Total: %{y:,}<extra></extra>"
        st.plotly_chart(fig_total, use_container_width=True)

    with tab_b:
        st.caption("Manager share is calculated using the filtered subset across all currently selected fields, years, and occupations.")
        st.markdown("**2. Manager share by gender (% of each gender)**")
        manager_share["hover_total"] = manager_share["Total"]
        manager_share["hover_mgr"] = manager_share["Manager Count"]
        fig_mgr_share = px.bar(
            manager_share,
            x="Gender",
            y="Manager Share (%)",
            color="Gender",
            color_discrete_map={"Female": FEMALE_COLOR, "Male": MALE_COLOR},
            labels={"Manager Share (%)": "Manager share (%)"},
            custom_data=["hover_total", "hover_mgr"],
        )
        for trace in fig_mgr_share.data:
            if trace.name == "Female":
                trace.name = f"Female{ratio_label}"
            trace.hovertemplate = (
                "Gender: %{x}<br>"
                "Manager share: %{y:.1f}%<br>"
                "Managers: %{customdata[1]:,}<br>"
                "Total: %{customdata[0]:,}<extra></extra>"
            )
        st.plotly_chart(fig_mgr_share, use_container_width=True)

    with tab_c:
        st.markdown("**3. Occupation distribution by gender (share of each gender)**")
        occ_dist["hover_value"] = occ_dist["VALUE"]
        occ_dist["Total Occupation Count"] = occ_dist.groupby("Occupations")["VALUE"].transform("sum")
        fig_occ = px.bar(
            occ_dist,
            y="Occupations",
            x="Share (%)",
            color="Gender",
            barmode="group",
            custom_data=["Occupations", "hover_value", "Gender"],
        )
        fig_occ.update_layout(
            height=750,
            yaxis_title="Occupation",
            xaxis_title="Share of gender (%)",
            yaxis={"categoryorder": "array", "categoryarray": occ_dist.sort_values("Total Occupation Count")["Occupations"].unique()},
        )
        fig_occ.update_traces(
            hovertemplate=(
                "Occupation: %{customdata[0]}<br>"
                "Gender: %{customdata[2]}<br>"
                "Share: %{x:.1f}%<br>"
                "Count: %{customdata[1]:,}<extra></extra>"
            )
        )
        st.plotly_chart(fig_occ, use_container_width=True)

    with tab_d:
        st.markdown("**4. Manager share by gender per field of study**")
        st.caption("Within each field, this shows what share of each gender is in managerial roles, based on the current filters.")
        field_share["hover_total"] = field_share["Total"]
        field_share["hover_mgr"] = field_share["Manager Count"]
        fig_field = px.bar(
            field_share,
            x="Gender",
            y="Manager Share (%)",
            color="Gender",
            facet_col="Field of Study",
            facet_col_wrap=3,
            color_discrete_map={"Female": FEMALE_COLOR, "Male": MALE_COLOR},
            custom_data=["hover_total", "hover_mgr"],
        )
        for trace in fig_field.data:
            if trace.name == "Female":
                trace.name = f"Female{ratio_label}"
            trace.hovertemplate = (
                "Gender: %{x}<br>"
                "Manager share: %{y:.2f}%<br>"
                "Managers: %{customdata[1]:,}<br>"
                "Total: %{customdata[0]:,}<extra></extra>"
            )
        st.plotly_chart(fig_field, use_container_width=True)

    with tab_e:
        st.markdown("**5. Occupation trends over time (selected occupations)**")
        trends = (
            rq2_filtered
            .groupby(["Graduation Year", "Occupations", "Gender"], as_index=False)["VALUE"]
            .sum()
        )
        fig_trend = px.line(
            trends,
            x="Graduation Year",
            y="VALUE",
            color="Gender",
            line_dash="Occupations",
            markers=True,
            color_discrete_map={"Female": FEMALE_COLOR, "Male": MALE_COLOR},
            custom_data=["Occupations", "Gender"],
        )
        fig_trend.update_traces(
            hovertemplate=(
                "Year: %{x}<br>"
                "Occupation: %{customdata[0]}<br>"
                "Gender: %{customdata[1]}<br>"
                "Count: %{y:,}<extra></extra>"
            )
        )
        fig_trend.update_layout(yaxis_title="Graduate count")
        st.plotly_chart(fig_trend, use_container_width=True)

# ================================
# RQ3: PLACEHOLDER / FUTURE DATASET
# ================================
with rq3_tab:
    st.header("RQ3 – Gender earnings gap over time")
    st.markdown(
        "**Research Question:** What is the gender earnings gap among health graduates, and how does "
        "it evolve over years since graduation? _Focus: Track median weekly earnings trajectories "
        "for male vs. female graduates across 1–13 years post-graduation._"
    )
    st.text_area("RQ3 Findings / Notes", value="", height=120, key="rq3_findings")

    DATA_PATH_RQ3 = BASE_DIR / "cleaned" / "rq3" / "rq3_earnings_clean.csv"
    rq3_df = load_rq3_data(DATA_PATH_RQ3)

    # ---- RQ3 SIDEBAR FILTERS ----
    with st.sidebar:
        with st.expander("RQ3 Filters", expanded=True):
            st.caption("Tick the fields of study to include. Charts update instantly.")
            field_options_rq3 = sorted(rq3_df["Field of Study"].unique())
            selected_fields_rq3 = []
            for field in field_options_rq3:
                checked = st.checkbox(
                    field,
                    value=st.session_state.get(f"rq3_field_{field}", True),
                    key=f"rq3_field_{field}",
                )
                if checked:
                    selected_fields_rq3.append(field)

    rq3_filtered = rq3_df[rq3_df["Field of Study"].isin(selected_fields_rq3)]

    if rq3_filtered.empty:
        st.warning("No data for the selected RQ3 fields of study.")
        st.stop()

    st.subheader("Earnings scatter by graduation year")
    st.markdown(
        "Each tab holds one graduation cohort (2010–2022). X-axis is years since graduation; "
        "Y-axis is median weekly earnings. Pink dots = female, blue dots = male. A small horizontal "
        "jitter separates overlapping gender points; marker shape shows field of study."
    )

    year_tabs = st.tabs([str(year) for year in range(2010, 2023)])

    for tab, year in zip(year_tabs, range(2010, 2023)):
        with tab:
            cohort = rq3_filtered[rq3_filtered["Graduation Year"] == year].copy()
            if cohort.empty:
                st.info("No data for the selected fields in this graduation year.")
                continue

            jitter_map = {"Female": 0.1, "Male": -0.1}
            cohort["Years since Graduation (jittered)"] = cohort["Years since Graduation"] + cohort["Gender"].map(jitter_map).fillna(0)
            x_ticks = sorted(cohort["Years since Graduation"].unique())

            fig_scatter = px.scatter(
                cohort,
                x="Years since Graduation (jittered)",
                y="VALUE",
                color="Gender",
                color_discrete_map={"Female": FEMALE_COLOR, "Male": MALE_COLOR},
                symbol="Field of Study",
                labels={
                    "Years since Graduation (jittered)": "Years since graduation (with small jitter)",
                    "VALUE": "Median weekly earnings",
                    "Gender": "Gender",
                },
                custom_data=["Years since Graduation", "Field of Study", "Graduation Year", "Gender"],
            )
            fig_scatter.update_traces(
                marker=dict(size=9, line=dict(width=0.5, color="white"), opacity=0.85),
                hovertemplate=(
                    "Years since graduation: %{customdata[0]}<br>"
                    "Earnings: €%{y:.0f}<br>"
                    "Gender: %{customdata[3]}<br>"
                    "Field: %{customdata[1]}<br>"
                    "Graduation year: %{customdata[2]}<extra></extra>"
                ),
            )
            fig_scatter.update_layout(
                xaxis_title="Years since graduation (jittered for clarity)",
                yaxis_title="Median weekly earnings",
                legend_title_text="Gender",
                xaxis=dict(tickmode="array", tickvals=x_ticks, ticktext=[str(t) for t in x_ticks]),
            )
            st.plotly_chart(fig_scatter, use_container_width=True)
