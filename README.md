# WattMinds

### AI-Powered Energy Optimization and Intelligent Decision Support System

WattMinds is a full-stack energy analytics application that transforms electricity consumption data into forecasts, anomaly alerts, cost estimates, and actionable recommendations. It combines a Python/FastAPI backend with an interactive HTML, CSS, and JavaScript dashboard, machine-learning models, appliance-level analysis, and weather-aware guidance.

The project is designed as a decision-support prototype: it helps users understand energy use and explore possible savings, but it does not directly control electrical equipment or measure consumption through a live smart meter.

## Key Features

| Module | What it does | Implementation |
| --- | --- | --- |
| Energy Dashboard | Presents energy metrics and analysis results in a responsive interface with 3D-style visual effects. | HTML, CSS, JavaScript |
| Consumption Forecasting | Estimates next-hour consumption from historical hourly energy readings. | Random Forest Regressor |
| Statistical Anomaly Detection | Flags readings that deviate significantly from a historical baseline. | Rolling median and median absolute deviation |
| ML Pattern Lab | Identifies unusual consumption observations in uploaded data. | Isolation Forest |
| Appliance Studio | Estimates appliance-wise daily/monthly usage, cost, and possible savings. | Python calculations |
| Energy Copilot | Routes supported energy questions to analysis tools and returns contextual responses. | Tool-based, rule-driven logic |
| Weather Advisor | Provides weather-related energy suggestions for selected appliances. | Open-Meteo API |
| What-If Simulator | Estimates the impact of changes in appliance usage and energy tariffs. | Scenario-based calculations |

> **AI capability note:** The Energy Copilot is currently a tool-based assistant, not a generative-LLM chatbot. ML anomaly flags indicate unusual observations; they are not proof of equipment faults or electricity waste.

## Technology Stack

| Layer | Technologies |
| --- | --- |
| Frontend | HTML5, CSS3, JavaScript |
| Backend | Python, FastAPI, Uvicorn |
| Machine learning | scikit-learn, Random Forest, Isolation Forest |
| Data processing | pandas, NumPy |
| Model persistence | joblib |
| External data | Open-Meteo API |
| Development | Git, GitHub, VS Code |

## System Architecture

```text
                 User / Browser
                       |
           HTML + CSS + JavaScript
                       |
                FastAPI REST API
                       |
     +-----------------+------------------+
     |                 |                  |
 Energy forecasting  Anomaly analysis  Appliance analysis
     |                 |                  |
 Random Forest     Rolling statistics  Usage/cost formulas
                   Isolation Forest
     +-----------------+------------------+
                       |
           Tool-based Energy Copilot
                       |
         Recommendations and scenarios
                       |
               Web dashboard

           Open-Meteo weather data
                | (as needed)
            Weather Advisor
```

## Machine Learning Workflow

### Energy forecasting

Historical electricity data is cleaned, checked for timestamp continuity, aggregated into hourly records, and converted into time-based and lagged features. A Random Forest regression pipeline estimates next-hour consumption.

Features used by the saved forecasting pipeline:

- `Hour_of_Day`, `Day_of_Week`, `Day_of_Month`, `Month`, `Is_Weekend`
- `Lag_1h`, `Lag_2h`, `Lag_24h`
- `Rolling_Mean_3h`, `Rolling_Mean_24h`

### Anomaly detection

The application includes two complementary approaches:

1. **Statistical detection:** compares energy readings with a rolling historical median and measures deviations using median absolute deviation (MAD).
2. **Isolation Forest:** an unsupervised model fitted on supplied consumption data to identify uncommon observations and patterns.

Anomalies should be reviewed in context; unusual readings may reflect legitimate changes in usage.

### Forecasting evaluation

The project's recorded test-set results for the historical household dataset are:

| Metric | Result |
| --- | ---: |
| Mean Absolute Error (MAE) | ~0.414 kWh |
| Root Mean Squared Error (RMSE) | ~0.583 kWh |
| R-squared (R²) | ~0.554 |
| Weighted Absolute Percentage Error (WAPE) | ~43.99% |

These results describe evaluation on the development dataset, not accuracy guaranteed for other households or facilities.

## Project Structure

```text
WattMinds/
├── backend/
│   ├── __init__.py
│   └── main.py
├── frontend/
│   ├── index.html
│   ├── styles.css
│   └── app.js
├── src/
│   ├── anomaly_detector.py
│   ├── csv_processor.py
│   ├── energy_agent.py
│   ├── energy_predictor.py
│   ├── energy_recommender.py
│   ├── manual_energy_agent.py
│   ├── weather_energy_agent.py
│   └── app.py
├── notebooks/              # Data validation, EDA and ML experiments
├── data/                   # Local datasets; excluded from Git
├── models/                 # Local trained models; excluded from Git
├── outputs/                # Locally generated outputs
├── requirements-web.txt
└── README.md
```

The original `src/app.py` is a Streamlit implementation retained in the project; the primary web interface is served through FastAPI and `frontend/`.

## Getting Started

### Prerequisites

- Python 3.10 or later (use a version compatible with the saved scikit-learn model)
- Git
- An internet connection for weather lookups
- A compatible trained model for ML forecasting

### 1. Clone the repository

```bash
git clone https://github.com/utkarsh6392/WattMinds_AI.git
cd WattMinds_AI
```

### 2. Create and activate a virtual environment

On Windows PowerShell:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

On macOS/Linux:

```bash
python3 -m venv .venv
source .venv/bin/activate
```

### 3. Install dependencies

```bash
python -m pip install -r requirements-web.txt
```

If your environment is missing a scientific-computing dependency used by the local modules, install the compatible version for your saved model. Model artifacts created with different scikit-learn versions may not load reliably.

### 4. Set up data and model files

Large datasets and trained model artifacts are intentionally not tracked in Git. For forecasting, provide the compatible model file at:

```text
models/final_energy_prediction_model.joblib
```

For CSV-based forecasting, provide hourly energy data in the format expected by the existing CSV processor, including `Hour` and `Energy_kWh` columns and enough consecutive hourly readings to calculate lag and rolling features. Some analysis notebooks require the original local datasets.

**Note:** Cloning this repository alone will not reproduce the trained model without access to the corresponding dataset and training artifacts.

### 5. Run the web application

From the project root:

```bash
python -m uvicorn backend.main:app --reload
```

Open **http://127.0.0.1:8000** in your browser. The FastAPI API documentation, if enabled, is available at **http://127.0.0.1:8000/docs**.

## Example Use Cases

- **Household monitoring:** inspect consumption trends, identify unusual readings, and estimate monthly appliance costs.
- **Energy-saving exploration:** change appliance operating hours and compare projected savings before making decisions.
- **Forecasting experiments:** upload supported hourly energy data to estimate near-term demand.
- **Weather-aware recommendations:** explore how local conditions may affect cooling or lighting usage.

## Limitations

- The forecasting model was trained on historical single-household electricity data; generalization to other facilities is limited.
- The current application is not connected to a live smart meter or IoT control system.
- Appliance costs and potential savings are estimates based on user-provided assumptions.
- Unsupervised and statistical anomaly detectors surface possible outliers but do not determine their underlying causes.
- The Energy Copilot uses structured tool routing and does not independently reason through an external LLM.
- Weather information requires access to a third-party API.
- Large training datasets and model files are not included in this GitHub repository.

## Future Improvements

- LLM-powered assistant with auditable tool calls and explanations
- Explainable ML predictions and feature contributions
- Live smart-meter and IoT integrations
- Advanced time-series forecasting and peak-demand estimation
- User accounts, saved facilities, and historical comparisons
- Downloadable reports and automated energy alerts
- Renewable energy and solar-generation analysis

## Project Information

**Type:** Academic major project / energy analytics prototype  
**Status:** Active development  
**Repository:** [github.com/utkarsh6392/WattMinds_AI](https://github.com/utkarsh6392/WattMinds_AI)

---

*WattMinds — Turning Energy Data into Informed Decisions.*
