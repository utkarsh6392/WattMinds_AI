from pathlib import Path

import numpy as np
import pandas as pd
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go


# ============================================================
# WATTMinds | ENERGY OPTIMIZATION DASHBOARD
# Premium, minimal, data-first interface
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = PROJECT_ROOT / "data"
OUTPUT_DIR = PROJECT_ROOT / "outputs"

HOURLY_PATH = DATA_DIR / "hourly_energy_data.csv"
RECOMMENDATIONS_PATH = OUTPUT_DIR / "energy_recommendations.csv"
FORECAST_PATH = OUTPUT_DIR / "next_hour_energy_forecast.csv"
MODEL_COMPARISON_PATH = OUTPUT_DIR / "final_test_model_comparison.csv"
SAVINGS_PATH = OUTPUT_DIR / "energy_savings_scenarios.csv"

st.set_page_config(
    page_title="WattMinds | Energy Intelligence",
    page_icon=None,
    layout="wide",
    initial_sidebar_state="expanded",
)

# -------------------- DESIGN SYSTEM --------------------

st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700&family=Manrope:wght@400;500;600;700;800&display=swap');

    :root {
        --ink: #172B3A;
        --muted: #6D7C88;
        --teal: #167D78;
        --teal-soft: #E5F3F0;
        --canvas: #F5F7F8;
        --line: #E3E9EC;
        --white: #FFFFFF;
    }

    html, body, [class*="css"] {
        font-family: 'DM Sans', sans-serif;
    }

    .stApp {
        background: var(--canvas);
        color: var(--ink);
    }

    [data-testid="stHeader"] {
        background: rgba(245,247,248,0.94);
    }

    [data-testid="stSidebar"] {
        background: #142735;
        border-right: 1px solid #243B49;
    }

    [data-testid="stSidebar"] * {
        color: #EAF0F3;
    }

    [data-testid="stSidebar"] label,
    [data-testid="stSidebar"] .stCaption {
        color: #B8C7CF !important;
    }

    [data-testid="stSidebar"] input,
    [data-testid="stSidebar"] [data-baseweb="select"] > div {
        background: #203846;
        border-color: #38505D;
    }

    .block-container {
        max-width: 1500px;
        padding-top: 2.0rem;
        padding-bottom: 3rem;
    }

    .brand-row {
        display: flex;
        align-items: center;
        gap: 12px;
        margin: 0 0 28px 0;
    }

    .brand-mark {
        width: 34px;
        height: 34px;
        border: 1px solid #6CAFA7;
        border-radius: 10px;
        display: flex;
        align-items: center;
        justify-content: center;
        color: #8AD0C3;
        font-family: 'Manrope', sans-serif;
        font-size: 17px;
        font-weight: 800;
        letter-spacing: -1px;
    }

    .brand-name {
        font-family: 'Manrope', sans-serif;
        font-size: 20px;
        font-weight: 800;
        letter-spacing: -0.8px;
        color: #FFFFFF;
    }

    .brand-sub {
        color: #A9BBC4;
        font-size: 10px;
        letter-spacing: 1.7px;
        text-transform: uppercase;
        margin-top: 1px;
    }

    .eyebrow {
        color: var(--teal);
        font-size: 11px;
        font-weight: 700;
        letter-spacing: 1.8px;
        text-transform: uppercase;
        margin-bottom: 8px;
    }

    .page-title {
        color: var(--ink);
        font-family: 'Manrope', sans-serif;
        font-size: clamp(29px, 3vw, 39px);
        font-weight: 800;
        letter-spacing: -1.7px;
        line-height: 1.12;
        margin: 0;
    }

    .page-subtitle {
        color: var(--muted);
        font-size: 14px;
        line-height: 1.65;
        margin-top: 10px;
        max-width: 760px;
    }

    .section-heading {
        font-family: 'Manrope', sans-serif;
        color: var(--ink);
        font-size: 19px;
        font-weight: 800;
        letter-spacing: -0.5px;
        margin: 8px 0 3px 0;
    }

    .section-subtitle {
        color: var(--muted);
        font-size: 12px;
        margin-bottom: 16px;
    }

    .kpi-card {
        background: #FFFFFF;
        border: 1px solid var(--line);
        border-radius: 15px;
        padding: 18px 19px 16px 19px;
        min-height: 128px;
        box-shadow: 0 3px 12px rgba(22, 43, 58, 0.025);
    }

    .kpi-label {
        color: #71818C;
        font-size: 11px;
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: 1.0px;
    }

    .kpi-value {
        color: var(--ink);
        font-family: 'Manrope', sans-serif;
        font-size: clamp(23px, 2vw, 30px);
        font-weight: 800;
        letter-spacing: -1px;
        margin-top: 11px;
        line-height: 1.1;
    }

    .kpi-foot {
        color: #82909A;
        font-size: 11px;
        margin-top: 8px;
    }

    .panel {
        background: #FFFFFF;
        border: 1px solid var(--line);
        border-radius: 15px;
        padding: 19px 20px 12px 20px;
        box-shadow: 0 3px 12px rgba(22, 43, 58, 0.025);
    }

    .forecast-card {
        background: #142D3B;
        border-radius: 16px;
        padding: 23px 24px;
        color: white;
        min-height: 250px;
    }

    .forecast-label {
        color: #A9C3C9;
        font-size: 11px;
        font-weight: 700;
        letter-spacing: 1.4px;
        text-transform: uppercase;
    }

    .forecast-number {
        color: #FFFFFF;
        font-family: 'Manrope', sans-serif;
        font-size: 39px;
        font-weight: 800;
        letter-spacing: -1.6px;
        margin-top: 12px;
    }

    .forecast-unit {
        color: #C1D1D6;
        font-size: 13px;
        font-weight: 500;
    }

    .forecast-divider {
        height: 1px;
        background: #34505D;
        margin: 18px 0;
    }

    .forecast-meta {
        color: #C2D1D6;
        font-size: 12px;
        line-height: 1.8;
    }

    .status-pill {
        display: inline-block;
        border-radius: 20px;
        background: #D9EEE8;
        color: #176B60;
        padding: 5px 10px;
        font-size: 11px;
        font-weight: 700;
        letter-spacing: 0.3px;
    }

    .recommendation {
        background: #FFFFFF;
        border: 1px solid var(--line);
        border-left: 3px solid var(--teal);
        border-radius: 10px;
        padding: 13px 15px;
        margin-bottom: 10px;
    }

    .recommendation-title {
        color: var(--ink);
        font-size: 13px;
        font-weight: 700;
        margin-bottom: 4px;
    }

    .recommendation-text {
        color: #6D7C88;
        font-size: 12px;
        line-height: 1.55;
    }

    .footer {
        color: #82909A;
        font-size: 11px;
        border-top: 1px solid var(--line);
        padding-top: 16px;
        margin-top: 32px;
    }

    div[data-testid="stMetric"] {
        background: #FFFFFF;
        border: 1px solid var(--line);
        padding: 15px 17px;
        border-radius: 13px;
    }

    div[data-testid="stMetricLabel"] {
        color: #71818C;
    }

    div[data-testid="stMetricValue"] {
        color: var(--ink);
        font-family: 'Manrope', sans-serif;
    }

    .stButton button, .stDownloadButton button {
        border-radius: 9px;
        font-weight: 700;
    }

    hr {
        border-color: var(--line);
    }
    </style>
    """,
    unsafe_allow_html=True,
)


# -------------------- HELPERS --------------------

def money(value):
    return f"₹{value:,.2f}"


def load_csv(path, required=True):
    if not path.exists():
        if required:
            st.error(f"Required file not found: `{path}`")
            st.stop()
        return None
    try:
        return pd.read_csv(path)
    except Exception as exc:
        st.error(f"Could not read `{path.name}`: {exc}")
        st.stop()


def plot_layout(fig, height=320):
    fig.update_layout(
        height=height,
        margin=dict(l=8, r=8, t=22, b=8),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(family="DM Sans, sans-serif", color="#6D7C88", size=11),
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="left",
            x=0,
            font=dict(size=10),
        ),
        hoverlabel=dict(
            bgcolor="#142D3B",
            bordercolor="#142D3B",
            font=dict(color="white", family="DM Sans"),
        ),
    )
    fig.update_xaxes(
        showgrid=False,
        linecolor="#E3E9EC",
        tickfont=dict(size=10),
    )
    fig.update_yaxes(
        showgrid=True,
        gridcolor="#EDF1F3",
        zeroline=False,
        tickfont=dict(size=10),
    )
    return fig


def section(title, subtitle=None):
    st.markdown(f'<div class="section-heading">{title}</div>', unsafe_allow_html=True)
    if subtitle:
        st.markdown(
            f'<div class="section-subtitle">{subtitle}</div>',
            unsafe_allow_html=True,
        )


def kpi_card(label, value, foot):
    st.markdown(
        f"""
        <div class="kpi-card">
            <div class="kpi-label">{label}</div>
            <div class="kpi-value">{value}</div>
            <div class="kpi-foot">{foot}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


# -------------------- LOAD DATA --------------------

hourly = load_csv(HOURLY_PATH)
recommendations = load_csv(RECOMMENDATIONS_PATH, required=False)
forecast_data = load_csv(FORECAST_PATH, required=False)
model_comparison = load_csv(MODEL_COMPARISON_PATH, required=False)

if "Hour" not in hourly.columns or "Energy_kWh" not in hourly.columns:
    st.error("hourly_energy_data.csv must contain Hour and Energy_kWh columns.")
    st.stop()

hourly["Hour"] = pd.to_datetime(hourly["Hour"], errors="coerce")
hourly["Energy_kWh"] = pd.to_numeric(hourly["Energy_kWh"], errors="coerce")
hourly = hourly.dropna(subset=["Hour", "Energy_kWh"]).sort_values("Hour")
hourly = hourly.drop_duplicates(subset=["Hour"], keep="last")

hourly["Hour_of_Day"] = hourly["Hour"].dt.hour
hourly["Day_of_Week"] = hourly["Hour"].dt.dayofweek
hourly["Day_Name"] = hourly["Hour"].dt.day_name()
hourly["Date"] = hourly["Hour"].dt.date
hourly["Month"] = hourly["Hour"].dt.to_period("M").astype(str)

if recommendations is not None:
    if "Hour" in recommendations.columns:
        recommendations["Hour"] = pd.to_datetime(
            recommendations["Hour"], errors="coerce"
        )

if forecast_data is not None and not forecast_data.empty:
    for col in ["Forecast_Hour", "Latest_Observed_Hour"]:
        if col in forecast_data.columns:
            forecast_data[col] = pd.to_datetime(
                forecast_data[col], errors="coerce"
            )


# -------------------- SIDEBAR --------------------

with st.sidebar:
    st.markdown(
        """
        <div class="brand-row">
            <div class="brand-mark">W</div>
            <div>
                <div class="brand-name">WattMinds</div>
                <div class="brand-sub">Energy Intelligence</div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown("### Workspace")
    st.caption("Explore consumption, forecasts and savings scenarios.")

    min_date = hourly["Hour"].min().date()
    max_date = hourly["Hour"].max().date()

    selected_dates = st.date_input(
        "Analysis period",
        value=(min_date, max_date),
        min_value=min_date,
        max_value=max_date,
        help="Choose the historical date range to analyse.",
    )

    st.markdown("---")
    st.markdown("### Cost assumptions")

    tariff = st.number_input(
        "Electricity tariff (₹ / kWh)",
        min_value=0.0,
        max_value=1000.0,
        value=8.0,
        step=0.5,
        help="Illustrative rate. Enter your applicable tariff for a better estimate.",
    )

    reduction_percent = st.slider(
        "What-if consumption reduction",
        min_value=0,
        max_value=30,
        value=10,
        step=5,
        format="%d%%",
    )

    st.markdown("---")
    st.caption("WATTMinds · Household Energy Analytics")
    st.caption("Historical data: Dec 2006 – Dec 2008")


if isinstance(selected_dates, tuple) and len(selected_dates) == 2:
    start_date, end_date = selected_dates
else:
    start_date = selected_dates
    end_date = selected_dates

filtered = hourly[
    (hourly["Hour"].dt.date >= start_date)
    & (hourly["Hour"].dt.date <= end_date)
].copy()

if filtered.empty:
    st.warning("No records exist in the selected date range.")
    st.stop()


# -------------------- PAGE HEADER --------------------

st.markdown('<div class="eyebrow">ENERGY PERFORMANCE / OVERVIEW</div>', unsafe_allow_html=True)
st.markdown('<h1 class="page-title">Energy Optimization Dashboard</h1>', unsafe_allow_html=True)
st.markdown(
    """
    <div class="page-subtitle">
        A clear view of household electricity consumption, predictive insights
        and practical opportunities to improve energy efficiency.
    </div>
    """,
    unsafe_allow_html=True,
)

st.markdown("")


# -------------------- KPI CARDS --------------------

total_energy = filtered["Energy_kWh"].sum()
mean_energy = filtered["Energy_kWh"].mean()
peak_idx = filtered["Energy_kWh"].idxmax()
peak_row = filtered.loc[peak_idx]
estimated_cost = total_energy * tariff
active_days = filtered["Hour"].dt.date.nunique()

c1, c2, c3, c4 = st.columns(4)

with c1:
    kpi_card("Total energy", f"{total_energy:,.1f} kWh", f"{len(filtered):,} recorded hours")

with c2:
    kpi_card("Average hourly use", f"{mean_energy:.3f} kWh", "Mean consumption in selected period")

with c3:
    kpi_card("Peak recorded hour", f"{peak_row['Energy_kWh']:.2f} kWh", peak_row["Hour"].strftime("%d %b %Y · %H:%M"))

with c4:
    kpi_card("Estimated energy cost", money(estimated_cost), f"At ₹{tariff:.2f} per kWh · {active_days} calendar days")

st.markdown("")


# -------------------- TREND + FORECAST --------------------

left, right = st.columns([1.65, 1], gap="large")

with left:
    section("Consumption trend", "Hourly energy use across the selected analysis period.")

    daily = (
        filtered.assign(Date=filtered["Hour"].dt.floor("D"))
        .groupby("Date", as_index=False)
        .agg(
            Daily_Energy_kWh=("Energy_kWh", "sum"),
            Average_Hourly_kWh=("Energy_kWh", "mean"),
        )
    )

    fig = go.Figure()
    fig.add_trace(
        go.Scatter(
            x=daily["Date"],
            y=daily["Daily_Energy_kWh"],
            mode="lines",
            name="Daily energy",
            line=dict(color="#167D78", width=2.2),
            fill="tozeroy",
            fillcolor="rgba(22,125,120,0.09)",
            hovertemplate="%{x|%d %b %Y}<br>%{y:.2f} kWh<extra></extra>",
        )
    )
    fig.update_layout(
        yaxis_title="Energy (kWh/day)",
        xaxis_title=None,
        showlegend=False,
    )
    fig = plot_layout(fig, 335)
    st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})

with right:
    section("Next-hour forecast", "Output from the saved Hist Gradient Boosting model.")

    if forecast_data is not None and not forecast_data.empty:
        fr = forecast_data.iloc[0]

        predicted = pd.to_numeric(
            pd.Series([fr.get("Predicted_Energy_kWh", np.nan)]),
            errors="coerce",
        ).iloc[0]
        baseline = pd.to_numeric(
            pd.Series([fr.get("Historical_Hour_Baseline_kWh", np.nan)]),
            errors="coerce",
        ).iloc[0]
        forecast_cost = predicted * tariff if pd.notna(predicted) else np.nan
        predicted_text = f"{predicted:.2f}" if pd.notna(predicted) else "—"
        forecast_time = fr.get("Forecast_Hour", None)
        level = str(fr.get("Consumption_Level", "Not available"))

        st.markdown(
            f"""
            <div class="forecast-card">
                <div class="forecast-label">Predicted energy</div>
                <div class="forecast-number">{predicted_text} <span class="forecast-unit">kWh</span></div>
                <div style="margin-top:12px;"><span class="status-pill">{level}</span></div>
                <div class="forecast-divider"></div>
                <div class="forecast-meta">
                    Forecast time: {forecast_time.strftime('%d %b %Y, %H:%M') if pd.notna(forecast_time) else 'Not available'}<br>
                    Historical hour baseline: {baseline:.2f} kWh<br>
                    Estimated cost at selected tariff: {money(forecast_cost) if pd.notna(forecast_cost) else 'Not available'}
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        st.caption(
            "Forecast uses the historical dataset's final available feature row. "
            "It is not a live reading or a current real-world forecast."
        )
    else:
        st.info("Forecast output not found. Run the recommendation engine first.")


st.markdown("")


# -------------------- HOURLY + WEEKDAY PATTERNS --------------------

section("Usage patterns", "Identify when energy demand tends to be higher.")

pattern_left, pattern_right = st.columns(2, gap="large")

with pattern_left:
    hourly_pattern = (
        filtered.groupby("Hour_of_Day", as_index=False)
        .agg(Average_Energy_kWh=("Energy_kWh", "mean"))
    )

    fig_hour = px.bar(
        hourly_pattern,
        x="Hour_of_Day",
        y="Average_Energy_kWh",
        labels={
            "Hour_of_Day": "Hour of day",
            "Average_Energy_kWh": "Average energy (kWh)",
        },
    )
    fig_hour.update_traces(
        marker_color="#167D78",
        marker_line_width=0,
        hovertemplate="Hour %{x}:00<br>Average %{y:.3f} kWh<extra></extra>",
    )
    fig_hour.update_xaxes(dtick=2)
    fig_hour = plot_layout(fig_hour, 300)
    st.plotly_chart(fig_hour, use_container_width=True, config={"displayModeBar": False})

with pattern_right:
    day_order = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
    weekday_pattern = (
        filtered.groupby("Day_Name", as_index=False)
        .agg(Average_Energy_kWh=("Energy_kWh", "mean"))
    )
    weekday_pattern["Day_Name"] = pd.Categorical(
        weekday_pattern["Day_Name"], categories=day_order, ordered=True
    )
    weekday_pattern = weekday_pattern.sort_values("Day_Name")

    fig_day = px.bar(
        weekday_pattern,
        x="Day_Name",
        y="Average_Energy_kWh",
        labels={
            "Day_Name": "Day of week",
            "Average_Energy_kWh": "Average energy (kWh)",
        },
    )
    fig_day.update_traces(
        marker_color="#5B7C91",
        marker_line_width=0,
        hovertemplate="%{x}<br>Average %{y:.3f} kWh/hour<extra></extra>",
    )
    fig_day = plot_layout(fig_day, 300)
    st.plotly_chart(fig_day, use_container_width=True, config={"displayModeBar": False})


# -------------------- MONTHLY PERFORMANCE --------------------

st.markdown("")
section("Monthly performance", "Total recorded energy by month within the selected period.")

monthly = (
    filtered.groupby("Month", as_index=False)
    .agg(
        Total_Energy_kWh=("Energy_kWh", "sum"),
        Average_Hourly_kWh=("Energy_kWh", "mean"),
        Recorded_Hours=("Energy_kWh", "size"),
    )
)

fig_month = go.Figure()
fig_month.add_trace(
    go.Bar(
        x=monthly["Month"],
        y=monthly["Total_Energy_kWh"],
        name="Total energy",
        marker_color="#167D78",
        hovertemplate="%{x}<br>%{y:,.1f} kWh<extra></extra>",
    )
)
fig_month.update_layout(
    xaxis_title=None,
    yaxis_title="Total energy (kWh)",
    showlegend=False,
)
fig_month = plot_layout(fig_month, 310)
st.plotly_chart(fig_month, use_container_width=True, config={"displayModeBar": False})


# -------------------- SAVINGS SIMULATOR --------------------

st.markdown("")
section("Energy savings simulator", "Illustrative scenarios based on the selected historical period.")

saving_energy = total_energy * (reduction_percent / 100)
saving_cost = saving_energy * tariff
after_energy = total_energy - saving_energy
after_cost = estimated_cost - saving_cost

s1, s2, s3, s4 = st.columns(4)

with s1:
    kpi_card("Reduction scenario", f"{reduction_percent}%", "User-selected what-if scenario")

with s2:
    kpi_card("Potential energy saved", f"{saving_energy:,.1f} kWh", "Estimated for selected period")

with s3:
    kpi_card("Potential cost saved", money(saving_cost), "At selected electricity tariff")

with s4:
    kpi_card("Energy after reduction", f"{after_energy:,.1f} kWh", "Illustrative, not measured savings")

scenario_df = pd.DataFrame([
    {
        "Scenario": f"{p}% reduction",
        "Energy_Saved_kWh": total_energy * p / 100,
        "Estimated_Cost_Saved_Rs": total_energy * p / 100 * tariff,
        "Energy_After_Reduction_kWh": total_energy * (1 - p / 100),
    }
    for p in [5, 10, 15, 20, 25, 30]
])

fig_saving = px.bar(
    scenario_df,
    x="Scenario",
    y="Estimated_Cost_Saved_Rs",
    labels={
        "Scenario": "Consumption reduction",
        "Estimated_Cost_Saved_Rs": "Estimated cost saved (₹)",
    },
)
fig_saving.update_traces(
    marker_color="#5B7C91",
    hovertemplate="%{x}<br>Estimated savings ₹%{y:,.2f}<extra></extra>",
)
fig_saving = plot_layout(fig_saving, 270)
st.plotly_chart(fig_saving, use_container_width=True, config={"displayModeBar": False})


# -------------------- RECOMMENDATIONS --------------------

st.markdown("")
section("Energy recommendations", "Historical flags are prompts for review, not proof of energy waste.")

if recommendations is not None and not recommendations.empty:
    if "Hour" in recommendations.columns:
        rec_filtered = recommendations[
            recommendations["Hour"].dt.date.between(start_date, end_date)
        ].copy()
    else:
        rec_filtered = recommendations.copy()

    if not rec_filtered.empty and "Consumption_Level" in rec_filtered.columns:
        priority = {"Unusually high": 0, "High": 1, "Normal": 2, "Low": 3}
        rec_filtered["_priority"] = rec_filtered["Consumption_Level"].map(priority).fillna(4)
        rec_filtered = rec_filtered.sort_values(
            ["_priority", "Hour"] if "Hour" in rec_filtered.columns else ["_priority"],
            ascending=[True, False] if "Hour" in rec_filtered.columns else [True],
        )

        if "Hour" in rec_filtered.columns:
            rec_filtered["Hour"] = rec_filtered["Hour"].dt.strftime("%Y-%m-%d %H:%M")

        display_columns = [
            col for col in [
                "Hour",
                "Energy_kWh",
                "Historical_Hour_Baseline_kWh",
                "Deviation_Percent",
                "Consumption_Level",
                "Estimated_Cost_Rs",
                "Recommendation",
            ]
            if col in rec_filtered.columns
        ]

        st.dataframe(
            rec_filtered[display_columns].head(20),
            use_container_width=True,
            hide_index=True,
            column_config={
                "Energy_kWh": st.column_config.NumberColumn("Energy (kWh)", format="%.3f"),
                "Historical_Hour_Baseline_kWh": st.column_config.NumberColumn("Hour baseline (kWh)", format="%.3f"),
                "Deviation_Percent": st.column_config.NumberColumn("Deviation (%)", format="%.1f%%"),
                "Estimated_Cost_Rs": st.column_config.NumberColumn("Estimated cost (₹)", format="₹%.2f"),
                "Recommendation": st.column_config.TextColumn("Suggested action", width="large"),
            },
        )

        csv_bytes = rec_filtered[display_columns].to_csv(index=False).encode("utf-8")
        st.download_button(
            "Export filtered recommendations",
            data=csv_bytes,
            file_name="wattminds_filtered_recommendations.csv",
            mime="text/csv",
        )
    else:
        st.info("No recommendation records available for this date range.")
else:
    st.info("Recommendation file not found. Run the energy recommendation engine first.")


# -------------------- MODEL PERFORMANCE --------------------

st.markdown("")
section("Predictive model performance", "Final test-set results from the saved model evaluation.")

if model_comparison is not None and not model_comparison.empty:
    st.dataframe(
        model_comparison,
        use_container_width=True,
        hide_index=True,
        column_config={
            "MAE_kWh": st.column_config.NumberColumn("MAE (kWh)", format="%.4f"),
            "RMSE_kWh": st.column_config.NumberColumn("RMSE (kWh)", format="%.4f"),
            "R2": st.column_config.NumberColumn("R²", format="%.4f"),
            "WAPE_percent": st.column_config.NumberColumn("WAPE (%)", format="%.2f%%"),
        },
    )
    st.caption(
        "These are stored final test metrics. Changing the dashboard date filter "
        "does not retrain the model or recalculate its test-set performance."
    )
else:
    st.info("Final model comparison file not found.")


# -------------------- DOWNLOADS + FOOTER --------------------

st.markdown("")
section("Data export", "Download the data currently represented in the dashboard.")

export_left, export_right = st.columns(2)

with export_left:
    st.download_button(
        "Download selected hourly data",
        data=filtered.to_csv(index=False).encode("utf-8"),
        file_name="wattminds_selected_hourly_data.csv",
        mime="text/csv",
        use_container_width=True,
    )

with export_right:
    st.download_button(
        "Download monthly summary",
        data=monthly.to_csv(index=False).encode("utf-8"),
        file_name="wattminds_monthly_summary.csv",
        mime="text/csv",
        use_container_width=True,
    )

st.markdown(
    """
    <div class="footer">
        <strong>WattMinds</strong> &nbsp;·&nbsp; Household Energy Intelligence
        <br><br>
        Forecasts and savings scenarios are estimates based on historical data.
        They do not represent live meter readings, guaranteed savings, or appliance-level diagnosis.
    </div>
    """,
    unsafe_allow_html=True,
)
