"""
Delhi Air Quality — Cleaning Report & Interactive Explorer
============================================================
Reads the artifacts produced by `air_quality_cleaning.ipynb`:
    - cleaning_summary.json   (fast-loading cleaning report stats)
    - cleaned_wide.parquet    (one row per station+timestamp, used for filtering/EDA)
    - air_quality.db          (star-schema SQLite database, used for the SQL tab)

Run with:  streamlit run streamlit_app.py
"""

import json
import sqlite3
from pathlib import Path

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

# --------------------------------------------------------------------------
# Page config & light styling
# --------------------------------------------------------------------------
st.set_page_config(
    page_title="Delhi Air Quality — Cleaning & Explorer",
    page_icon="🌫️",
    layout="wide",
)

st.markdown("""
<style>
    .block-container {padding-top: 2rem;}
    [data-testid="stMetricValue"] {font-size: 1.6rem;}
    .stTabs [data-baseweb="tab"] {font-size: 1rem; padding: 0.5rem 1rem;}
</style>
""", unsafe_allow_html=True)

DATA_DIR = Path(__file__).parent
SUMMARY_PATH = DATA_DIR / "cleaning_summary.json"
WIDE_PATH = DATA_DIR / "cleaned_wide.parquet"
DB_PATH = DATA_DIR / "air_quality.db"

AQI_ORDER = ["Good", "Satisfactory", "Moderate", "Poor", "Very Poor", "Severe"]
AQI_COLORS = {
    "Good": "#4CAF50", "Satisfactory": "#8BC34A", "Moderate": "#FFC107",
    "Poor": "#FF9800", "Very Poor": "#F44336", "Severe": "#7B1FA2",
}
POLLUTANT_COLS = [
    "pm25_ugm3", "pm10_ugm3", "no2_ugm3", "no_ugm3", "ozone_ugm3", "co_mgm3",
    "so2_ugm3", "nh3_ugm3", "benzene_ugm3", "toluene_ugm3", "xylene_ugm3",
    "eth_benzene_ugm3", "mp_xylene_ugm3",
]


# --------------------------------------------------------------------------
# Data loading (cached)
# --------------------------------------------------------------------------
@st.cache_data
def load_summary():
    if not SUMMARY_PATH.exists():
        return None
    with open(SUMMARY_PATH) as f:
        return json.load(f)


@st.cache_data
def load_wide():
    if not WIDE_PATH.exists():
        return None
    w = pd.read_parquet(WIDE_PATH)
    w["datetime"] = pd.to_datetime(w["datetime"])
    return w


@st.cache_resource
def get_connection():
    if not DB_PATH.exists():
        return None
    return sqlite3.connect(str(DB_PATH), check_same_thread=False)


def missing_files_notice():
    st.error(
        "Couldn't find the data files this app needs. Place `cleaning_summary.json`, "
        "`cleaned_wide.parquet`, and `air_quality.db` (all produced by "
        "`air_quality_cleaning.ipynb`) in the same folder as this script, then rerun."
    )


summary = load_summary()
wide = load_wide()

st.title("🌫️ Delhi Air Quality — Cleaning Report & Explorer")
st.caption(
    "6 monitoring stations · 13 pollutants · Jan 2024 – Dec 2025 · 15-minute readings"
)

if summary is None or wide is None:
    missing_files_notice()
    st.stop()

tab_report, tab_explore, tab_model = st.tabs(
    ["📋 Cleaning Report", "📊 Explore the Data", "🗄️ Data Model & SQL"]
)

# ==========================================================================
# TAB 1 — Cleaning report (instant, reads only the small JSON summary)
# ==========================================================================
with tab_report:
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Raw rows", f"{summary['raw_shape'][0]:,}")
    c2.metric("Cleaned rows (long)", f"{summary['cleaned_long_shape'][0]:,}")
    c3.metric("Cleaned rows (wide)", f"{summary['cleaned_wide_shape'][0]:,}")
    c4.metric("Outliers flagged", f"{summary['total_outliers_flagged']:,}")

    st.markdown("---")

    col_a, col_b = st.columns([1, 1])

    with col_a:
        st.subheader("Columns dropped during cleaning")
        for col in summary["dropped_columns"]:
            st.markdown(f"- `{col}`")

        st.subheader("Stations without weather sensors")
        st.info(
            "These are pollutant-only (IMD) stations — their weather fields are "
            "genuinely absent, not a data-quality issue, so they were left as missing "
            "rather than imputed:\n\n"
            + "\n".join(f"- {s}" for s in summary["stations_without_weather_sensors"])
        )

        st.subheader("Date range covered")
        st.write(f"{summary['date_range'][0]}  →  {summary['date_range'][1]}")

    with col_b:
        st.subheader("Missing meteorological values: before vs. after interpolation")
        miss_df = pd.DataFrame({
            "column": list(summary["missing_before"].keys()),
            "before": list(summary["missing_before"].values()),
            "after": [summary["missing_after"][k] for k in summary["missing_before"]],
        })
        fig = go.Figure()
        fig.add_bar(name="Before", x=miss_df["column"], y=miss_df["before"], marker_color="#FF9800")
        fig.add_bar(name="After", x=miss_df["column"], y=miss_df["after"], marker_color="#4CAF50")
        fig.update_layout(barmode="group", height=380, margin=dict(t=10, b=10))
        st.plotly_chart(fig, width='stretch')
        st.caption(
            "Reduction comes from short DPCC-station sensor outages being interpolated. "
            "The remaining missing values belong to the two sensor-less IMD stations above."
        )

    st.markdown("---")
    st.subheader("Outliers flagged per pollutant (% of readings, IQR method)")
    out_df = pd.DataFrame({
        "pollutant": list(summary["outlier_pct_by_pollutant"].keys()),
        "outlier_pct": list(summary["outlier_pct_by_pollutant"].values()),
    }).sort_values("outlier_pct", ascending=True)
    fig2 = px.bar(out_df, x="outlier_pct", y="pollutant", orientation="h",
                  color="outlier_pct", color_continuous_scale="Oranges",
                  labels={"outlier_pct": "% flagged as outlier", "pollutant": ""})
    fig2.update_layout(height=420, margin=dict(t=10, b=10), coloraxis_showscale=False)
    st.plotly_chart(fig2, width='stretch')
    st.caption(
        "Outliers were **capped (winsorized)**, not deleted, so the time series stays "
        "continuous — see the notebook's Section 11 for the exact bounds per pollutant."
    )

# ==========================================================================
# TAB 2 — Interactive explorer (filters + charts on cleaned_wide.parquet)
# ==========================================================================
with tab_explore:
    st.sidebar.header("🔎 Filters")

    all_stations = sorted(wide["station_name"].unique().tolist())
    sel_stations = st.sidebar.multiselect("Stations", all_stations, default=all_stations)

    pollutant_labels = {c: c.replace("_ugm3", "").replace("_mgm3", "") for c in POLLUTANT_COLS}
    sel_pollutant = st.sidebar.selectbox(
        "Primary pollutant", POLLUTANT_COLS, index=0,
        format_func=lambda c: pollutant_labels[c].upper()
    )

    min_date, max_date = wide["datetime"].min().date(), wide["datetime"].max().date()
    date_range = st.sidebar.date_input(
        "Date range", value=(min_date, max_date), min_value=min_date, max_value=max_date
    )
    if isinstance(date_range, tuple) and len(date_range) == 2:
        start_date, end_date = date_range
    else:
        start_date, end_date = min_date, max_date

    sel_season = st.sidebar.multiselect(
        "Season", sorted(wide["season"].unique().tolist()),
        default=sorted(wide["season"].unique().tolist())
    )
    weekday_filter = st.sidebar.radio("Day type", ["All", "Weekday", "Weekend"], horizontal=False)

    mask = (
        wide["station_name"].isin(sel_stations)
        & wide["season"].isin(sel_season)
        & (wide["datetime"].dt.date >= start_date)
        & (wide["datetime"].dt.date <= end_date)
    )
    if weekday_filter == "Weekday":
        mask &= ~wide["is_weekend"]
    elif weekday_filter == "Weekend":
        mask &= wide["is_weekend"]

    fdf = wide.loc[mask]

    if fdf.empty:
        st.warning("No data matches the current filters — widen your selection.")
        st.stop()

    label = pollutant_labels[sel_pollutant].upper()
    unit = "mg/m³" if sel_pollutant == "co_mgm3" else "µg/m³"

    k1, k2, k3, k4 = st.columns(4)
    k1.metric(f"Avg {label}", f"{fdf[sel_pollutant].mean():.1f} {unit}")
    k2.metric(f"Max {label}", f"{fdf[sel_pollutant].max():.1f} {unit}")
    k3.metric("Rows in selection", f"{len(fdf):,}")
    k4.metric("Stations in selection", f"{fdf['station_name'].nunique()}")

    st.markdown("---")
    st.subheader(f"{label} over time")
    daily = (fdf.set_index("datetime")
                .groupby([pd.Grouper(freq="D"), "station_name"])[sel_pollutant]
                .mean().reset_index())
    fig3 = px.line(daily, x="datetime", y=sel_pollutant, color="station_name",
                    labels={sel_pollutant: f"{label} ({unit})", "datetime": ""})
    fig3.update_layout(height=420, legend_title="Station", margin=dict(t=10))
    st.plotly_chart(fig3, width='stretch')

    col_c, col_d = st.columns(2)

    with col_c:
        st.subheader("Station comparison")
        st_avg = fdf.groupby("station_name")[sel_pollutant].mean().sort_values()
        fig4 = px.bar(st_avg, orientation="h",
                      labels={"value": f"Avg {label} ({unit})", "station_name": ""},
                      color=st_avg.values, color_continuous_scale="Reds")
        fig4.update_layout(height=380, showlegend=False, coloraxis_showscale=False, margin=dict(t=10))
        st.plotly_chart(fig4, width='stretch')

    with col_d:
        st.subheader("Weekday vs weekend")
        wk = fdf.groupby(fdf["is_weekend"].map({True: "Weekend", False: "Weekday"}))[sel_pollutant].mean()
        fig5 = px.bar(wk, labels={"value": f"Avg {label} ({unit})", "index": ""}, color=wk.index)
        fig5.update_layout(height=380, showlegend=False, margin=dict(t=10))
        st.plotly_chart(fig5, width='stretch')

    st.markdown("---")
    col_e, col_f = st.columns(2)

    with col_e:
        st.subheader("Weather vs pollutant correlation")
        corr_candidates = ["at_c", "rh_percent", "ws_m_s", "bp_mmhg"] + POLLUTANT_COLS
        corr_cols = [c for c in corr_candidates if c in fdf.columns]
        corr = fdf[corr_cols].corr(numeric_only=True)
        fig6 = px.imshow(corr, color_continuous_scale="RdBu_r", zmin=-1, zmax=1,
                          labels=dict(color="correlation"))
        fig6.update_layout(height=480, margin=dict(t=10))
        st.plotly_chart(fig6, width='stretch')

    with col_f:
        if f"{pollutant_labels[sel_pollutant]}" in ["pm25", "pm10", "no2", "so2", "co", "ozone", "nh3"]:
            st.subheader(f"{label} AQI category mix")
            # Recompute category quickly from the cleaned value using the same breakpoints
            # used in the notebook would require the long table; instead this chart simply
            # buckets the *raw* concentration into rough bands to keep the app self-contained.
            st.caption("Approximate bands for a quick read — see the notebook for the exact CPCB sub-index.")
            bins = pd.qcut(fdf[sel_pollutant].dropna(), q=5, duplicates="drop")
            band_counts = bins.value_counts().sort_index()
            fig7 = px.bar(x=band_counts.index.astype(str), y=band_counts.values,
                          labels={"x": f"{label} range ({unit})", "y": "Readings"})
            fig7.update_layout(height=480, margin=dict(t=10))
            st.plotly_chart(fig7, width='stretch')
        else:
            st.subheader("Value distribution")
            fig7 = px.histogram(fdf, x=sel_pollutant, nbins=40,
                                 labels={sel_pollutant: f"{label} ({unit})"})
            fig7.update_layout(height=480, margin=dict(t=10))
            st.plotly_chart(fig7, width='stretch')

    st.markdown("---")
    with st.expander("📥 Download filtered data"):
        st.dataframe(fdf.head(100), width='stretch', height=250)
        st.download_button(
            "Download filtered selection as CSV",
            data=fdf.to_csv(index=False).encode("utf-8"),
            file_name="filtered_air_quality.csv",
            mime="text/csv",
        )

# ==========================================================================
# TAB 3 — Data model & SQL explorer (reads the star-schema SQLite DB)
# ==========================================================================
with tab_model:
    st.subheader("Star-schema data model")
    st.markdown("""
The cleaned dataset is loaded into `air_quality.db` as a small star schema:

- **`dim_station`** — station_key, station_id, station_name, state, city
- **`dim_pollutant`** — pollutant_key, pollutant
- **`dim_time`** — time_key, datetime, year, month, day, hour, day_of_week, is_weekend, season
- **`fact_air_quality`** — one row per reading, linked to the three dimensions via surrogate
  keys, plus `value`, `value_clean`, `is_outlier`, `aqi_sub_index`, `aqi_category`, and the
  weather columns
""")

    conn = get_connection()
    if conn is None:
        st.warning("`air_quality.db` not found next to this app — the SQL explorer needs it.")
        st.stop()

    preset_queries = {
        "Average PM2.5 / PM10 by station": """
            SELECT s.station_name, p.pollutant, ROUND(AVG(f.value_clean), 1) AS avg_value
            FROM fact_air_quality f
            JOIN dim_station s ON f.station_key = s.station_key
            JOIN dim_pollutant p ON f.pollutant_key = p.pollutant_key
            WHERE p.pollutant IN ('pm25', 'pm10')
            GROUP BY s.station_name, p.pollutant
            ORDER BY s.station_name, p.pollutant;
        """,
        "Monthly AQI category counts (PM2.5)": """
            SELECT t.year, t.month, f.aqi_category, COUNT(*) AS n
            FROM fact_air_quality f
            JOIN dim_time t ON f.time_key = t.time_key
            JOIN dim_pollutant p ON f.pollutant_key = p.pollutant_key
            WHERE p.pollutant = 'pm25'
            GROUP BY t.year, t.month, f.aqi_category
            ORDER BY t.year, t.month;
        """,
        "Outlier rate by pollutant": """
            SELECT p.pollutant, ROUND(100.0 * AVG(f.is_outlier), 2) AS outlier_pct
            FROM fact_air_quality f
            JOIN dim_pollutant p ON f.pollutant_key = p.pollutant_key
            GROUP BY p.pollutant
            ORDER BY outlier_pct DESC;
        """,
    }

    choice = st.selectbox("Try a preset query, or write your own below:", list(preset_queries.keys()))
    query_text = st.text_area("SQL (SELECT-only)", value=preset_queries[choice].strip(), height=140)

    run = st.button("▶ Run query")
    if run:
        cleaned = query_text.strip().rstrip(";")
        if not cleaned.lower().startswith("select"):
            st.error("Only SELECT statements are allowed in this explorer.")
        else:
            try:
                result = pd.read_sql_query(cleaned, conn)
                st.dataframe(result, width='stretch', height=350)
                st.caption(f"{len(result):,} rows returned")
            except Exception as e:
                st.error(f"Query failed: {e}")
