
import streamlit as st
import pandas as pd

from energy_agent import predict_from_csv
from manual_energy_agent import run_energy_agent
from weather_energy_agent import get_weather_energy_advice


# =====================================================
# PAGE CONFIGURATION
# =====================================================

st.set_page_config(
    page_title="WattMinds | Energy Intelligence",
    page_icon="⚡",
    layout="wide",
)

st.title("⚡ WattMinds")
st.subheader("AI-Powered Energy Optimization")

st.write(
    "Analyze electricity consumption, forecast demand, "
    "and discover practical energy-saving opportunities "
    "using appliance analysis, machine learning, and weather data."
)


# =====================================================
# NAVIGATION
# =====================================================

mode = st.radio(
    "Choose your input method",
    [
        "Manual Appliance Entry",
        "CSV Upload (ML Prediction)",
        "Weather-Aware Energy Agent",
    ],
    horizontal=True,
)

st.divider()


# =====================================================
# MODE 1: MANUAL APPLIANCE ENTRY
# =====================================================

if mode == "Manual Appliance Entry":

    st.header("🔌 Appliance Energy Analysis")

    st.write(
        "Enter your appliances and let WattMinds analyze "
        "their consumption, prioritize actions, and estimate "
        "potential savings."
    )

    tariff = st.number_input(
        "Electricity tariff (₹ per kWh)",
        min_value=0.0,
        value=8.0,
        step=0.5,
        key="manual_tariff",
    )

    target_savings = st.number_input(
        "Monthly savings goal (₹)",
        min_value=0.0,
        value=500.0,
        step=100.0,
        key="target_savings",
    )

    number_of_appliances = st.number_input(
        "Number of appliance types",
        min_value=1,
        max_value=20,
        value=3,
        step=1,
        key="appliance_count",
    )

    appliance_data = []

    default_names = [
        "Air Conditioner",
        "Refrigerator",
        "LED Bulb",
    ]

    default_watts = [1500.0, 200.0, 9.0]
    default_hours = [6.0, 8.0, 6.0]
    default_quantities = [1, 1, 4]

    with st.form("appliance_form"):

        st.caption(
            "Enter rated power in watts, approximate daily usage "
            "hours, and the number of appliances."
        )

        for i in range(int(number_of_appliances)):

            st.markdown(f"#### Appliance {i + 1}")

            col1, col2, col3, col4 = st.columns(4)

            with col1:
                name = st.text_input(
                    "Appliance name",
                    value=(
                        default_names[i]
                        if i < len(default_names)
                        else ""
                    ),
                    key=f"name_{i}",
                )

            with col2:
                watts = st.number_input(
                    "Rated watts",
                    min_value=0.0,
                    max_value=100000.0,
                    value=(
                        default_watts[i]
                        if i < len(default_watts)
                        else 100.0
                    ),
                    step=1.0,
                    key=f"watts_{i}",
                )

            with col3:
                hours = st.number_input(
                    "Hours per day",
                    min_value=0.0,
                    max_value=24.0,
                    value=(
                        default_hours[i]
                        if i < len(default_hours)
                        else 1.0
                    ),
                    step=0.5,
                    key=f"hours_{i}",
                )

            with col4:
                quantity = st.number_input(
                    "Quantity",
                    min_value=1,
                    max_value=100,
                    value=(
                        default_quantities[i]
                        if i < len(default_quantities)
                        else 1
                    ),
                    step=1,
                    key=f"quantity_{i}",
                )

            appliance_data.append({
                "Appliance": name.strip() or f"Appliance {i + 1}",
                "Rated Power (W)": watts,
                "Hours/Day": hours,
                "Quantity": quantity,
            })

        submitted = st.form_submit_button(
            "🤖 Analyze & Generate Action Plan",
            type="primary",
            use_container_width=True,
        )

    if submitted:

        try:
            df = pd.DataFrame(appliance_data)

            result = run_energy_agent(
                appliances=df,
                tariff=tariff,
                target_savings=target_savings,
            )

            st.success("WattMinds analysis completed!")

            st.header("📊 Energy Overview")

            col1, col2, col3, col4 = st.columns(4)

            col1.metric(
                "Daily Consumption",
                f"{result['total_daily_energy_kwh']:.2f} kWh",
            )

            col2.metric(
                "Monthly Consumption",
                f"{result['total_monthly_energy_kwh']:.2f} kWh",
            )

            col3.metric(
                "Estimated Monthly Bill",
                f"₹{result['total_monthly_cost']:.2f}",
            )

            col4.metric(
                "Potential Monthly Savings",
                f"₹{result['projected_savings']:.2f}",
            )

            st.divider()

            st.header("🤖 WattMinds Energy Advisor")

            st.write(result["summary"])

            st.caption(
                "The advisor ranks appliances using estimated "
                "energy consumption and generates rule-based "
                "recommendations from your inputs."
            )

            if result["top_appliance"] is not None:
                st.info(
                    f"Priority appliance: {result['top_appliance']}"
                )

            st.subheader("Appliance Consumption Analysis")

            st.dataframe(
                result["analysis"],
                use_container_width=True,
                hide_index=True,
            )

            st.subheader("🧠 Recommended Actions")

            if result["recommendations"]:

                rec_df = pd.DataFrame(result["recommendations"])

                st.dataframe(
                    rec_df,
                    use_container_width=True,
                    hide_index=True,
                )

            else:
                st.info(
                    "Enter positive power ratings and usage hours "
                    "to generate recommendations."
                )

            st.subheader("🎯 Goal-Based Action Plan")

            st.write(
                f"Your monthly savings goal is "
                f"₹{result['target_savings']:.2f}."
            )

            if result["target_achieved"]:
                st.success(
                    "The selected scenarios meet the entered "
                    "savings target under the current assumptions."
                )
            else:
                st.warning(
                    "The available scenarios do not meet your "
                    "savings goal. Consider reviewing additional "
                    "appliances or adjusting the target."
                )

            if result["action_plan"]:

                plan_df = pd.DataFrame(result["action_plan"])

                st.dataframe(
                    plan_df,
                    use_container_width=True,
                    hide_index=True,
                )

            else:
                st.info(
                    "No positive savings scenarios were found "
                    "for the entered values."
                )

            st.subheader("💡 What-If Savings Simulator")

            monthly_energy = result["total_monthly_energy_kwh"]
            monthly_cost = result["total_monthly_cost"]

            scenarios = []

            for reduction in [5, 10, 15, 20]:

                energy_saved = monthly_energy * reduction / 100
                cost_saved = monthly_cost * reduction / 100

                scenarios.append({
                    "Usage Reduction (%)": reduction,
                    "Estimated Energy Saved (kWh/month)": round(
                        energy_saved, 2
                    ),
                    "Estimated Cost Saved (₹/month)": round(
                        cost_saved, 2
                    ),
                    "Estimated Remaining Bill (₹)": round(
                        monthly_cost - cost_saved, 2
                    ),
                })

            st.dataframe(
                pd.DataFrame(scenarios),
                use_container_width=True,
                hide_index=True,
            )

            st.caption(
                "Savings are hypothetical estimates, not guarantees. "
                "The manual advisor uses predefined rules and "
                "your entered appliance details."
            )

        except Exception as error:
            st.error(f"Energy analysis failed: {error}")


# =====================================================
# MODE 2: CSV UPLOAD + ML FORECAST
# =====================================================

elif mode == "CSV Upload (ML Prediction)":

    st.header("📂 Hourly Energy Forecast")

    st.write(
        "Upload historical hourly readings to use the "
        "existing machine-learning forecasting pipeline."
    )

    uploaded_file = st.file_uploader(
        "Upload your hourly energy CSV",
        type=["csv"],
        key="energy_csv",
    )

    tariff = st.number_input(
        "Electricity tariff (₹ per kWh)",
        min_value=0.0,
        value=8.0,
        step=0.5,
        key="csv_tariff",
    )

    if uploaded_file is not None:

        if st.button(
            "Analyze Energy Consumption",
            type="primary",
            key="analyze_csv",
        ):

            try:
                with st.spinner("Analyzing historical data..."):

                    result = predict_from_csv(
                        uploaded_file,
                        tariff=tariff,
                    )

                st.success("Forecast completed successfully!")

                col1, col2, col3 = st.columns(3)

                col1.metric(
                    "Predicted Energy",
                    f"{result['predicted_energy_kwh']:.4f} kWh",
                )

                col2.metric(
                    "Forecast Hour",
                    str(result["forecast_hour"]),
                )

                rec = result["recommendations"]

                col3.metric(
                    "Estimated Cost",
                    f"₹{rec['estimated_cost_rs']:.2f}",
                )

                st.subheader("Energy Intelligence")

                st.write(
                    "**Consumption Level:**",
                    rec["consumption_level"],
                )

                st.write(
                    "**Historical Average:**",
                    f"{rec['historical_average_kwh']:.4f} kWh",
                )

                st.info(rec["recommendation"])

                st.subheader("What-If Savings Scenarios")

                savings_df = pd.DataFrame(
                    rec["savings_scenarios"]
                )

                savings_df = savings_df.rename(
                    columns={
                        "reduction_percent": "Reduction (%)",
                        "estimated_energy_saved_kwh":
                            "Energy Saved (kWh)",
                        "estimated_cost_saved":
                            "Estimated Cost Saved (₹)",
                    }
                )

                st.dataframe(
                    savings_df,
                    use_container_width=True,
                    hide_index=True,
                )

                st.caption(
                    "Forecasts are estimates based on the model's "
                    "historical training data. Manual appliance "
                    "inputs are not used by this forecasting model."
                )

            except Exception as error:
                st.error(f"CSV analysis failed: {error}")


# =====================================================
# MODE 3: WEATHER-AWARE ENERGY AGENT
# =====================================================

elif mode == "Weather-Aware Energy Agent":

    st.header("🌦️ Weather-Aware Energy Agent")

    st.write(
        "Get current weather information and practical "
        "energy-saving suggestions for ACs, fans, and lights."
    )

    st.info(
        "This agent generates recommendations. It does not "
        "automatically switch appliances on or off."
    )

    city = st.text_input(
        "Enter your city",
        value="Ghaziabad",
        key="weather_city",
        placeholder="e.g. Ghaziabad, Delhi, Lucknow",
    )

    st.subheader("🏠 Appliances in your home")

    st.caption(
        "Select the appliances you want the agent to consider."
    )

    col1, col2, col3 = st.columns(3)

    with col1:
        has_ac = st.checkbox("Air Conditioner (AC)", value=True)

    with col2:
        has_fan = st.checkbox("Fan", value=True)

    with col3:
        has_lights = st.checkbox("Lights / Bulbs", value=True)

    if st.button(
        "🤖 Run Weather & Energy Agent",
        type="primary",
        use_container_width=True,
    ):

        try:
            appliance_names = []

            if has_ac:
                appliance_names.append("Air Conditioner")

            if has_fan:
                appliance_names.append("Fan")

            if has_lights:
                appliance_names.append("LED Bulb")

            weather_appliances = pd.DataFrame({
                "Appliance": appliance_names
            })

            with st.spinner(
                "Fetching weather and generating recommendations..."
            ):
                result = get_weather_energy_advice(
                    city=city,
                    appliances=weather_appliances,
                )

            st.success("Weather analysis completed!")

            st.subheader("🌡️ Current Weather")

            col1, col2, col3 = st.columns(3)

            col1.metric(
                "Temperature",
                f"{result['temperature_c']:.1f} °C",
            )

            humidity = result["humidity_percent"]

            col2.metric(
                "Humidity",
                f"{humidity}%" if humidity is not None else "N/A",
            )

            col3.metric(
                "Day / Night",
                "Daytime" if result["is_day"] else "Night",
            )

            st.write(
                f"**Location:** {result['city']}, {result['country']}"
            )

            st.write(
                f"**Local time:** {result['local_time']}"
            )

            col1, col2 = st.columns(2)

            with col1:
                st.write(
                    f"🌅 **Sunrise:** {result['sunrise'] or 'N/A'}"
                )

            with col2:
                st.write(
                    f"🌇 **Sunset:** {result['sunset'] or 'N/A'}"
                )

            st.divider()

            st.subheader("🧠 Agent Recommendations")

            for alert in result["alerts"]:

                title = alert["Title"]
                priority = alert["Priority"]

                message = (
                    f"**Reason:** {alert['Reason']}\n\n"
                    f"**Recommended action:** {alert['Action']}"
                )

                if priority == "High":
                    st.warning(
                        f"🔴 **{title} — High Priority**\n\n{message}"
                    )

                elif priority == "Review":
                    st.info(
                        f"🟡 **{title} — Review**\n\n{message}"
                    )

                else:
                    st.success(
                        f"🟢 **{title} — Normal**\n\n{message}"
                    )

            st.caption(
                "Advice is based on outdoor weather and the selected "
                "appliances. Outdoor temperature may differ from "
                "indoor conditions. Check comfort and safety before "
                "changing appliance usage."
            )

        except Exception as error:
            st.error(
                f"Weather analysis failed: {error}"
            )
