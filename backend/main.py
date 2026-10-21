"""WattMinds 2.0: FastAPI bridge to the existing src/ Python modules.

Run from the WattMinds project root:
    python -m uvicorn backend.main:app --reload
"""
from __future__ import annotations

import io
import os
import sys
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.encoders import jsonable_encoder
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

PROJECT_ROOT = Path(__file__).resolve().parent.parent
SRC_DIR = PROJECT_ROOT / "src"
FRONTEND_DIR = PROJECT_ROOT / "frontend"
sys.path.insert(0, str(SRC_DIR))
os.chdir(PROJECT_ROOT)

app = FastAPI(title="WattMinds 2.0 API", version="0.1.0")
MAX_FILE_BYTES = 15 * 1024 * 1024


class Appliance(BaseModel):
    name: str = Field(min_length=1)
    watts: float = Field(ge=0)
    hours: float = Field(ge=0, le=24)
    quantity: int = Field(ge=1, le=100)


class ManualRequest(BaseModel):
    appliances: list[Appliance] = Field(min_length=1)
    tariff: float = Field(default=8.0, ge=0)
    target_savings: float = Field(default=500.0, ge=0)


class WeatherRequest(BaseModel):
    city: str = Field(min_length=2)
    appliances: list[str] = Field(default_factory=list)
    tariff: float = Field(default=8.0, ge=0)


def safe_value(value: Any) -> Any:
    if isinstance(value, pd.DataFrame):
        return [safe_value(r) for r in value.head(150).to_dict(orient="records")]
    if isinstance(value, pd.Series):
        return {str(k): safe_value(v) for k, v in value.to_dict().items()}
    if isinstance(value, dict):
        return {str(k): safe_value(v) for k, v in value.items()}
    if isinstance(value, (list, tuple, set)):
        return [safe_value(x) for x in value]
    if isinstance(value, (np.integer,)):
        return int(value)
    if isinstance(value, (np.floating, float)):
        return float(value) if np.isfinite(value) else None
    if isinstance(value, (np.bool_,)):
        return bool(value)
    if isinstance(value, (pd.Timestamp,)):
        return str(value)
    try:
        return jsonable_encoder(value)
    except Exception:
        return str(value)


async def csv_bytes(file: UploadFile) -> bytes:
    if not file.filename or not file.filename.lower().endswith(".csv"):
        raise HTTPException(400, detail="Please upload a .csv file.")
    content = await file.read(MAX_FILE_BYTES + 1)
    if len(content) > MAX_FILE_BYTES:
        raise HTTPException(413, detail="CSV file must be 15 MB or smaller.")
    if not content:
        raise HTTPException(400, detail="The CSV file is empty.")
    return content


@app.get("/api/health")
def health():
    return {
        "status": "ok",
        "src_found": SRC_DIR.is_dir(),
        "model_found": (PROJECT_ROOT / "models" / "final_energy_prediction_model.joblib").is_file(),
        "modules": sorted(p.name for p in SRC_DIR.glob("*.py")) if SRC_DIR.exists() else [],
    }


@app.post("/api/manual")
def manual_analysis(request: ManualRequest):
    from manual_energy_agent import run_energy_agent

    # Translate web-form names into the exact existing module column names.
    df = pd.DataFrame([
        {
            "Appliance": appliance.name,
            "Rated Power (W)": appliance.watts,
            "Hours/Day": appliance.hours,
            "Quantity": appliance.quantity,
        }
        for appliance in request.appliances
    ])
    try:
        report = run_energy_agent(df, request.tariff, request.target_savings)
        return {"status": "success", "result": safe_value(report)}
    except Exception as error:
        raise HTTPException(422, detail=f"Manual analyzer error: {error}") from error


@app.post("/api/weather")
def weather_analysis(request: WeatherRequest):
    from weather_energy_agent import get_weather_energy_advice

    try:
        # The existing agent accepts appliance names; pass only selected names.
        report = get_weather_energy_advice(
            request.city.strip(), appliances=request.appliances, tariff=request.tariff
        )
        return {"status": "success", "result": safe_value(report)}
    except Exception as error:
        raise HTTPException(422, detail=f"Weather agent error: {error}") from error


@app.post("/api/forecast")
async def forecast_csv(file: UploadFile = File(...), tariff: float = 8.0):
    from energy_agent import predict_from_csv

    content = await csv_bytes(file)
    if tariff < 0:
        raise HTTPException(400, detail="Tariff cannot be negative.")
    source = io.BytesIO(content)
    source.name = file.filename  # for compatibility with Streamlit-style upload handlers
    try:
        report = predict_from_csv(source, tariff=tariff)
        return {"status": "success", "result": safe_value(report)}
    except Exception as error:
        raise HTTPException(422, detail=f"ML forecast error: {error}") from error


@app.post("/api/anomalies")
async def anomaly_csv(file: UploadFile = File(...)):
    from anomaly_detector import detect_energy_anomalies

    content = await csv_bytes(file)
    try:
        frame = pd.read_csv(io.BytesIO(content))
        cols = {str(col).strip().lower(): col for col in frame.columns}
        candidates = ("energy_kwh", "energy (kwh)", "consumption_kwh", "kwh", "energy")
        key = next((cols[c] for c in candidates if c in cols), None)
        if key is None:
            raise ValueError("Missing energy column. Expected Energy_kWh (hourly kWh).")
        frame = frame.rename(columns={key: "Energy_kWh"})
        result = detect_energy_anomalies(frame, column="Energy_kWh")
        anomalies = result[result["Anomaly"] == True].copy()
        count = len(anomalies)
        return {
            "status": "success",
            "result": {
                "rows_analyzed": len(result),
                "anomaly_count": count,
                "anomaly_rate_pct": round(count * 100 / len(result), 2) if len(result) else 0,
                "recent_readings": safe_value(result.tail(96)),
                "anomalies": safe_value(anomalies.tail(50)),
            },
        }
    except Exception as error:
        raise HTTPException(422, detail=f"Anomaly detection error: {error}") from error




class CopilotRequest(BaseModel):
    question: str = Field(min_length=3, max_length=600)
    appliances: list[Appliance] = Field(default_factory=list)
    tariff: float = Field(default=8.0, ge=0)


@app.post("/api/copilot")
def energy_copilot(request: CopilotRequest):
    """Transparent tool-routing decision assistant; no LLM or autonomous external actions."""
    question = request.question.lower()
    tools_used = []
    if not request.appliances:
        return {"status": "success", "result": {
            "answer": "Add your actual appliances (watts, usage hours, quantity) to get a data-backed answer. This assistant does not assume your energy use.",
            "tools_used": [], "type": "needs_data", "actions": []}}
    readings = []
    for item in request.appliances:
        daily = item.watts * item.hours * item.quantity / 1000
        readings.append({"name": item.name, "daily_kwh": daily,
                         "monthly_kwh": daily * 30, "monthly_cost": daily * 30 * request.tariff,
                         "watts": item.watts, "hours": item.hours, "quantity": item.quantity})
    readings.sort(key=lambda x: x["monthly_cost"], reverse=True)
    tools_used.append("appliance_energy_calculator")
    monthly = sum(x["monthly_cost"] for x in readings)
    top = readings[0]
    actions = []
    if any(word in question for word in ("save", "saving", "reduce", "cut", "optimiz", "कम", "बच", "tips", "suggest")):
        tools_used.append("scenario_optimizer")
        for item in readings[:3]:
            reduction = min(item["hours"], 1.0)
            saved_kwh = item["watts"] * item["quantity"] * reduction * 30 / 1000
            actions.append({"appliance":item["name"], "reduction_hours_per_day":reduction,
                            "monthly_kwh_saved":round(saved_kwh,2),
                            "monthly_inr_saved":round(saved_kwh * request.tariff,2)})
        if actions:
            best = max(actions, key=lambda x:x["monthly_inr_saved"])
            answer = (f"Your calculated 30-day baseline is ₹{monthly:,.2f}. "
                      f"The largest estimated 1-hour/day reduction is {best['appliance']}: "
                      f"₹{best['monthly_inr_saved']:,.2f}/month ({best['monthly_kwh_saved']:.2f} kWh). "
                      "These are theoretical reductions, not guaranteed savings. Keep essential cooling and safety needs in mind.")
        else:
            answer = "Not enough usage hours to estimate further reductions."
    elif any(word in question for word in ("most", "highest", "top", "maximum", "expensive", "which", "ज्यादा", "सबसे")):
        answer = (f"{top['name']} consumes the most among the entered appliances: "
                  f"{top['monthly_kwh']:.2f} kWh and ₹{top['monthly_cost']:,.2f} over 30 days. "
                  f"Your total modeled cost is ₹{monthly:,.2f}.")
    else:
        answer = (f"For the entered appliances, estimated consumption is "
                  f"{sum(x['monthly_kwh'] for x in readings):.2f} kWh over 30 days "
                  f"(₹{monthly:,.2f} at ₹{request.tariff:g}/kWh). "
                  f"Highest contributor: {top['name']} (₹{top['monthly_cost']:,.2f}). "
                  "Ask 'How can I save money?' for a usage-reduction simulation.")
    return {"status":"success", "result": {"answer":answer, "tools_used":tools_used,
            "type":"tool_based_decision_assistant", "monthly_cost_inr":round(monthly,2),
            "appliance_breakdown":readings, "actions":actions,
            "assumptions":"Rated power is constant, 30 days, flat tariff; no real-time metering."}}


@app.post("/api/ml-patterns")
async def ml_patterns(file: UploadFile = File(...), contamination: float = 0.05):
    """IsolationForest fitted per uploaded data; distinct from saved forecasting model."""
    from sklearn.ensemble import IsolationForest
    from sklearn.preprocessing import StandardScaler

    content = await csv_bytes(file)
    if not 0.01 <= contamination <= 0.2:
        raise HTTPException(400, detail="Contamination must be between 0.01 and 0.20")
    try:
        df = pd.read_csv(io.BytesIO(content))
        cols = {str(c).lower().strip(): c for c in df.columns}
        energy_col = next((cols[c] for c in ("energy_kwh", "consumption_kwh", "kwh", "energy") if c in cols), None)
        if energy_col is None:
            raise ValueError("CSV must include Energy_kWh, consumption_kwh, kwh or energy.")
        energies = pd.to_numeric(df[energy_col], errors="coerce")
        valid = energies.notna() & (energies >= 0)
        sample = df.loc[valid].copy().head(20000)
        sample["Energy_kWh"] = energies[valid].head(20000).to_numpy()
        if len(sample) < 50:
            raise ValueError("At least 50 valid energy readings are required.")
        # Hour is optional; fit on energy only if no trustworthy hour column is supplied.
        features = ["Energy_kWh"]
        hour_col = next((cols[c] for c in ("hour_of_day", "hour") if c in cols), None)
        if hour_col is not None:
            hours = pd.to_numeric(sample[hour_col], errors="coerce")
            if hours.notna().all() and hours.between(0,23).all():
                sample["hour_sin"] = np.sin(2*np.pi*hours/24)
                sample["hour_cos"] = np.cos(2*np.pi*hours/24)
                features += ["hour_sin", "hour_cos"]
        x = StandardScaler().fit_transform(sample[features])
        model = IsolationForest(n_estimators=120, contamination=contamination,
                                random_state=42, n_jobs=-1)
        sample["ml_outlier"] = model.fit_predict(x) == -1
        sample["anomaly_score"] = -model.decision_function(x)
        findings = sample[sample["ml_outlier"]].sort_values("anomaly_score", ascending=False)
        return {"status":"success", "result": {
            "method":"Isolation Forest (unsupervised, trained per upload)",
            "total_scanned":len(sample), "outliers":int(sample["ml_outlier"].sum()),
            "anomaly_fraction":round(float(sample["ml_outlier"].mean()),4),
            "features_used":features, "typical_energy_kwh":round(float(sample["Energy_kWh"].median()),3),
            "highest_outlier_examples":safe_value(findings[["Energy_kWh","anomaly_score"]].head(12)),
            "limitations":"Outliers are statistical, not confirmed faults. Upload must represent comparable readings; results depend on contamination. Limited to first 20,000 valid rows."}}
    except Exception as error:
        raise HTTPException(422, detail=f"ML pattern detection error: {error}") from error


@app.get("/")
def index():
    return FileResponse(FRONTEND_DIR / "index.html")


# Register AFTER API routes to keep /api endpoints accessible.
app.mount("/", StaticFiles(directory=str(FRONTEND_DIR)), name="frontend")
