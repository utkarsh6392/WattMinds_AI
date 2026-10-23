"""
WattMinds 2.0 — FastAPI Backend

Features:
- Supabase authentication
- Secure Bearer token verification
- ML energy forecasting
- Statistical anomaly detection
- Isolation Forest pattern analysis
- Appliance energy calculations
- Weather-aware recommendations
- Rule-based Energy Copilot
- Frontend static file serving
"""

from __future__ import annotations

import io
import json
import os
import sys
import urllib.error
import urllib.request

from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from dotenv import load_dotenv

from fastapi import (
    Depends,
    FastAPI,
    File,
    Header,
    HTTPException,
    UploadFile,
)

from fastapi.encoders import jsonable_encoder
from fastapi.responses import FileResponse, Response
from fastapi.staticfiles import StaticFiles

from pydantic import BaseModel, Field


# =========================================================
# 1. PROJECT CONFIGURATION
# =========================================================

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "src"
FRONTEND = ROOT / "frontend"

load_dotenv(ROOT / ".env")

sys.path.insert(0, str(SRC))

app = FastAPI(
    title="WattMinds API",
    description=(
        "AI-powered energy optimization and "
        "decision-support platform."
    ),
    version="2.0",
)

MAX_CSV_SIZE = 15 * 1024 * 1024

SUPABASE_URL = os.getenv(
    "SUPABASE_URL", ""
).strip().rstrip("/")

SUPABASE_PUBLISHABLE_KEY = os.getenv(
    "SUPABASE_PUBLISHABLE_KEY", ""
).strip()


# =========================================================
# 2. SUPABASE PUBLIC CONFIGURATION
# =========================================================

@app.get("/api/public-config")
def public_config():
    """
    Return browser-safe Supabase configuration.

    The publishable key is designed to be public.
    Never return a secret/service_role key here.
    """

    if not SUPABASE_URL or not SUPABASE_PUBLISHABLE_KEY:
        raise HTTPException(
            status_code=503,
            detail="Supabase is not configured."
        )

    return {
        "supabase_url": SUPABASE_URL,
        "supabase_publishable_key": (
            SUPABASE_PUBLISHABLE_KEY
        ),
    }


# =========================================================
# 3. SUPABASE TOKEN VERIFICATION
# =========================================================

def require_user(
    authorization: str | None = Header(default=None)
) -> dict:
    """
    Verify a user's Supabase access token.

    Supabase Auth's /auth/v1/user endpoint validates
    the access token and returns the authenticated user.

    This approach works with both legacy HS256 and
    newer asymmetric signing configurations.
    """

    if not SUPABASE_URL or not SUPABASE_PUBLISHABLE_KEY:
        raise HTTPException(
            status_code=503,
            detail="Supabase is not configured."
        )

    if not authorization:
        raise HTTPException(
            status_code=401,
            detail="Please log in to continue.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    scheme, separator, token = authorization.partition(" ")

    if (
        not separator
        or scheme.lower() != "bearer"
        or not token.strip()
    ):
        raise HTTPException(
            status_code=401,
            detail="Invalid authorization header.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    token = token.strip()

    request = urllib.request.Request(
        SUPABASE_URL + "/auth/v1/user",
        headers={
            "Authorization": f"Bearer {token}",
            "apikey": SUPABASE_PUBLISHABLE_KEY,
            "Accept": "application/json",
        },
        method="GET",
    )

    try:
        with urllib.request.urlopen(
            request,
            timeout=8
        ) as response:
            user = json.loads(response.read())

    except urllib.error.HTTPError as error:

        if error.code in (400, 401, 403):
            raise HTTPException(
                status_code=401,
                detail="Session invalid or expired.",
                headers={
                    "WWW-Authenticate": "Bearer"
                },
            ) from error

        raise HTTPException(
            status_code=502,
            detail="Authentication service unavailable."
        ) from error

    except (
        urllib.error.URLError,
        TimeoutError,
        ValueError,
    ) as error:

        raise HTTPException(
            status_code=503,
            detail="Cannot verify login right now."
        ) from error

    if not isinstance(user, dict) or not user.get("id"):
        raise HTTPException(
            status_code=401,
            detail="Invalid session.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return user


# =========================================================
# 4. REQUEST MODELS
# =========================================================

class Appliance(BaseModel):
    name: str = Field(min_length=1)
    watts: float = Field(ge=0)
    hours: float = Field(ge=0, le=24)
    quantity: int = Field(ge=1, le=100)


class ManualRequest(BaseModel):
    appliances: list[Appliance] = Field(min_length=1)
    tariff: float = Field(default=8, ge=0)
    target_savings: float = Field(
        default=500,
        ge=0
    )


class WeatherRequest(BaseModel):
    city: str = Field(min_length=2)
    appliances: list[str] = Field(
        default_factory=list
    )
    tariff: float = Field(default=8, ge=0)


class CopilotRequest(BaseModel):
    question: str = Field(
        min_length=3,
        max_length=600
    )
    appliances: list[Appliance] = Field(
        default_factory=list
    )
    tariff: float = Field(default=8, ge=0)


# =========================================================
# 5. JSON SERIALIZATION
# =========================================================

def safe_value(value: Any):
    """
    Convert Pandas / NumPy results into JSON-safe data.
    """

    if isinstance(value, pd.DataFrame):
        return [
            safe_value(row)
            for row in value.head(150).to_dict(
                orient="records"
            )
        ]

    if isinstance(value, pd.Series):
        return {
            str(key): safe_value(item)
            for key, item in value.to_dict().items()
        }

    if isinstance(value, dict):
        return {
            str(key): safe_value(item)
            for key, item in value.items()
        }

    if isinstance(value, (list, tuple, set)):
        return [
            safe_value(item)
            for item in value
        ]

    if isinstance(value, np.integer):
        return int(value)

    if isinstance(value, (float, np.floating)):
        return (
            float(value)
            if np.isfinite(value)
            else None
        )

    if isinstance(value, np.bool_):
        return bool(value)

    if isinstance(value, pd.Timestamp):
        return str(value)

    try:
        return jsonable_encoder(value)
    except Exception:
        return str(value)


# =========================================================
# 6. CSV UPLOAD VALIDATION
# =========================================================

async def read_csv(file: UploadFile):
    """
    Accept CSV uploads up to 15 MB.
    """

    if (
        not file.filename
        or not file.filename.lower().endswith(".csv")
    ):
        raise HTTPException(
            status_code=400,
            detail="Please upload a CSV file."
        )

    content = await file.read(MAX_CSV_SIZE + 1)

    if len(content) > MAX_CSV_SIZE:
        raise HTTPException(
            status_code=413,
            detail="CSV must be 15 MB or smaller."
        )

    if not content:
        raise HTTPException(
            status_code=400,
            detail="Uploaded CSV is empty."
        )

    return content


# =========================================================
# 7. PUBLIC HEALTH CHECK
# =========================================================

@app.get("/api/health")
def health():
    return {
        "status": "ok",
        "src_found": SRC.is_dir(),
        "model_found": (
            ROOT
            / "models"
            / "final_energy_prediction_model.joblib"
        ).is_file(),
        "modules": (
            sorted(
                path.name
                for path in SRC.glob("*.py")
            )
            if SRC.exists()
            else []
        ),
    }


# =========================================================
# 8. APPLIANCE ENERGY ANALYSIS
# =========================================================

@app.post(
    "/api/manual",
    dependencies=[Depends(require_user)]
)
def manual_analysis(request: ManualRequest):

    from manual_energy_agent import run_energy_agent

    data = pd.DataFrame([
        {
            "Appliance": item.name,
            "Rated Power (W)": item.watts,
            "Hours/Day": item.hours,
            "Quantity": item.quantity,
        }
        for item in request.appliances
    ])

    try:
        result = run_energy_agent(
            data,
            request.tariff,
            request.target_savings
        )

        return {
            "status": "success",
            "result": safe_value(result)
        }

    except Exception as error:
        raise HTTPException(
            status_code=422,
            detail=f"Manual analysis error: {error}"
        ) from error


# =========================================================
# 9. WEATHER ADVISOR
# =========================================================

@app.post(
    "/api/weather",
    dependencies=[Depends(require_user)]
)
def weather_analysis(request: WeatherRequest):

    from weather_energy_agent import (
        get_weather_energy_advice
    )

    try:
        # The weather module expects a DataFrame,
        # not a plain list of appliance names.
        appliance_table = pd.DataFrame({
            "Appliance": request.appliances,
            "name": request.appliances,
        })

        result = get_weather_energy_advice(
            city=request.city.strip(),
            appliances=appliance_table,
            tariff=request.tariff,
        )

        return {
            "status": "success",
            "result": safe_value(result)
        }

    except Exception as error:
        raise HTTPException(
            status_code=422,
            detail=f"Weather agent error: {error}"
        ) from error


# =========================================================
# 10. ML ENERGY FORECASTING
# =========================================================

@app.post(
    "/api/forecast",
    dependencies=[Depends(require_user)]
)
async def forecast_csv(
    file: UploadFile = File(...),
    tariff: float = 8.0,
):

    from energy_agent import predict_from_csv

    content = await read_csv(file)

    if not np.isfinite(tariff) or tariff < 0:
        raise HTTPException(
            status_code=400,
            detail="Tariff must be a nonnegative finite number."
        )

    source = io.BytesIO(content)
    source.name = file.filename

    try:
        result = predict_from_csv(
            source,
            tariff=tariff
        )

        return {
            "status": "success",
            "result": safe_value(result)
        }

    except Exception as error:
        raise HTTPException(
            status_code=422,
            detail=f"ML forecast error: {error}"
        ) from error


# =========================================================
# 11. STATISTICAL ANOMALY DETECTION
# =========================================================

@app.post(
    "/api/anomalies",
    dependencies=[Depends(require_user)]
)
async def anomaly_analysis(
    file: UploadFile = File(...)
):

    from anomaly_detector import (
        detect_energy_anomalies
    )

    content = await read_csv(file)

    try:
        df = pd.read_csv(io.BytesIO(content))

        columns = {
            str(column).strip().lower(): column
            for column in df.columns
        }

        candidates = (
            "energy_kwh",
            "energy (kwh)",
            "consumption_kwh",
            "kwh",
            "energy",
        )

        selected = next(
            (
                columns[name]
                for name in candidates
                if name in columns
            ),
            None
        )

        if selected is None:
            raise ValueError(
                "CSV must contain an Energy_kWh column."
            )

        df = df.rename(
            columns={selected: "Energy_kWh"}
        )

        result = detect_energy_anomalies(
            df,
            column="Energy_kWh"
        )

        anomalies = result[
            result["Anomaly"] == True
        ]

        count = len(anomalies)

        return {
            "status": "success",
            "result": {
                "rows_analyzed": len(result),
                "anomaly_count": count,
                "anomaly_rate_pct": (
                    round(
                        count * 100 / len(result),
                        2
                    )
                    if len(result)
                    else 0
                ),
                "recent_readings": safe_value(
                    result.tail(96)
                ),
                "anomalies": safe_value(
                    anomalies.tail(50)
                ),
            }
        }

    except Exception as error:
        raise HTTPException(
            status_code=422,
            detail=f"Anomaly detection error: {error}"
        ) from error


# =========================================================
# 12. ENERGY COPILOT
# =========================================================

@app.post(
    "/api/copilot",
    dependencies=[Depends(require_user)]
)
def energy_copilot(request: CopilotRequest):
    """
    Tool-based, rule-driven energy assistant.

    This is not a generative LLM chatbot.
    """

    question = request.question.lower().strip()

    if not request.appliances:
        return {
            "status": "success",
            "result": {
                "answer": (
                    "Enter appliance details to receive "
                    "energy calculations and recommendations."
                ),
                "tools_used": [],
                "actions": [],
                "type": "needs_data"
            }
        }

    readings = []

    for appliance in request.appliances:

        daily = (
            appliance.watts
            * appliance.hours
            * appliance.quantity
            / 1000
        )

        monthly_energy = daily * 30

        monthly_cost = (
            monthly_energy * request.tariff
        )

        readings.append({
            "name": appliance.name,
            "watts": appliance.watts,
            "hours": appliance.hours,
            "quantity": appliance.quantity,
            "daily_kwh": round(daily, 3),
            "monthly_kwh": round(
                monthly_energy,
                3
            ),
            "monthly_cost": round(
                monthly_cost,
                2
            ),
        })

    readings.sort(
        key=lambda item: item["monthly_cost"],
        reverse=True
    )

    total_cost = sum(
        item["monthly_cost"]
        for item in readings
    )

    total_energy = sum(
        item["monthly_kwh"]
        for item in readings
    )

    top = readings[0]

    tools_used = [
        "appliance_energy_calculator"
    ]

    actions = []

    saving_keywords = (
        "save",
        "saving",
        "reduce",
        "cut",
        "optimiz",
        "tips",
        "suggest",
        "कम",
        "बच"
    )

    ranking_keywords = (
        "most",
        "highest",
        "top",
        "maximum",
        "expensive",
        "which",
        "सबसे",
        "ज्यादा"
    )

    if any(
        word in question
        for word in saving_keywords
    ):

        tools_used.append(
            "scenario_optimizer"
        )

        for item in readings[:3]:

            reduction = min(
                item["hours"],
                1.0
            )

            saved_energy = (
                item["watts"]
                * item["quantity"]
                * reduction
                * 30
                / 1000
            )

            saved_money = (
                saved_energy * request.tariff
            )

            actions.append({
                "appliance": item["name"],
                "reduction_hours_per_day": reduction,
                "monthly_kwh_saved": round(
                    saved_energy,
                    2
                ),
                "monthly_inr_saved": round(
                    saved_money,
                    2
                ),
            })

        best = max(
            actions,
            key=lambda item: (
                item["monthly_inr_saved"]
            )
        )

        answer = (
            f"Your estimated monthly electricity cost is "
            f"₹{total_cost:,.2f} for "
            f"{total_energy:.2f} kWh. "
            f"Reducing {best['appliance']} usage by "
            f"{best['reduction_hours_per_day']:.1f} "
            f"hour/day could save approximately "
            f"₹{best['monthly_inr_saved']:,.2f} "
            "per month. These are estimates "
            "based on your inputs."
        )

    elif any(
        word in question
        for word in ranking_keywords
    ):

        answer = (
            f"{top['name']} is the highest-consuming "
            "entered appliance. "
            f"It uses approximately "
            f"{top['monthly_kwh']:.2f} kWh per month, "
            f"costing ₹{top['monthly_cost']:,.2f}. "
            f"Total estimated monthly cost is "
            f"₹{total_cost:,.2f}."
        )

    else:

        answer = (
            "Your entered appliances use approximately "
            f"{total_energy:.2f} kWh per month. "
            f"Estimated monthly cost: "
            f"₹{total_cost:,.2f} "
            f"at ₹{request.tariff:g}/kWh. "
            f"Highest contributor: {top['name']}."
        )

    return {
        "status": "success",
        "result": {
            "answer": answer,
            "tools_used": tools_used,
            "type": "tool_based_decision_assistant",
            "monthly_cost_inr": round(
                total_cost,
                2
            ),
            "appliance_breakdown": readings,
            "actions": actions,
            "assumptions": (
                "Rated power is constant, 30 days, "
                "flat tariff; no real-time metering."
            ),
        }
    }


# =========================================================
# 13. ML PATTERN LAB — ISOLATION FOREST
# =========================================================

@app.post(
    "/api/ml-patterns",
    dependencies=[Depends(require_user)]
)
async def ml_patterns(
    file: UploadFile = File(...),
    contamination: float = 0.05,
):

    from sklearn.ensemble import IsolationForest
    from sklearn.preprocessing import StandardScaler

    content = await read_csv(file)

    if (
        not np.isfinite(contamination)
        or not 0.01 <= contamination <= 0.20
    ):
        raise HTTPException(
            status_code=400,
            detail=(
                "Contamination must be "
                "between 0.01 and 0.20."
            )
        )

    try:
        df = pd.read_csv(io.BytesIO(content))

        columns = {
            str(column).strip().lower(): column
            for column in df.columns
        }

        energy_column = next(
            (
                columns[name]
                for name in (
                    "energy_kwh",
                    "consumption_kwh",
                    "kwh",
                    "energy",
                )
                if name in columns
            ),
            None
        )

        if energy_column is None:
            raise ValueError(
                "CSV must contain Energy_kWh "
                "or a compatible column."
            )

        energies = pd.to_numeric(
            df[energy_column],
            errors="coerce"
        )

        valid = (
            energies.notna()
            & (energies >= 0)
        )

        sample = (
            df.loc[valid]
            .copy()
            .head(20000)
        )

        sample["Energy_kWh"] = (
            energies[valid]
            .head(20000)
            .to_numpy()
        )

        if len(sample) < 50:
            raise ValueError(
                "At least 50 valid readings are required."
            )

        features = ["Energy_kWh"]

        hour_column = next(
            (
                columns[name]
                for name in (
                    "hour_of_day",
                    "hour"
                )
                if name in columns
            ),
            None
        )

        if hour_column is not None:

            hours = pd.to_numeric(
                sample[hour_column],
                errors="coerce"
            )

            if (
                hours.notna().all()
                and hours.between(0, 23).all()
            ):

                sample["hour_sin"] = np.sin(
                    2 * np.pi * hours / 24
                )

                sample["hour_cos"] = np.cos(
                    2 * np.pi * hours / 24
                )

                features += [
                    "hour_sin",
                    "hour_cos"
                ]

        X = StandardScaler().fit_transform(
            sample[features]
        )

        model = IsolationForest(
            n_estimators=120,
            contamination=contamination,
            random_state=42,
            n_jobs=-1,
        )

        sample["ml_outlier"] = (
            model.fit_predict(X) == -1
        )

        sample["anomaly_score"] = (
            -model.decision_function(X)
        )

        anomalies = (
            sample[sample["ml_outlier"]]
            .sort_values(
                "anomaly_score",
                ascending=False
            )
        )

        return {
            "status": "success",
            "result": {
                "method": "Isolation Forest",
                "total_scanned": len(sample),
                "outliers": int(
                    sample["ml_outlier"].sum()
                ),
                "anomaly_fraction": round(
                    float(
                        sample["ml_outlier"].mean()
                    ),
                    4
                ),
                "features_used": features,
                "typical_energy_kwh": round(
                    float(
                        sample["Energy_kWh"].median()
                    ),
                    3
                ),
                "highest_outlier_examples": safe_value(
                    anomalies[
                        [
                            "Energy_kWh",
                            "anomaly_score"
                        ]
                    ].head(12)
                ),
                "limitations": (
                    "Statistical outliers are not "
                    "confirmed faults. Analysis is "
                    "limited to the first 20,000 "
                    "valid rows."
                ),
            }
        }

    except Exception as error:
        raise HTTPException(
            status_code=422,
            detail=f"ML pattern error: {error}"
        ) from error


# =========================================================
# 13b. DEMO CSV DOWNLOAD (PUBLIC, SYNTHETIC DATA)
# =========================================================

@app.get("/api/demo-data")
def demo_data():
    """
    Download a synthetic hourly CSV for trying the app.

    Public on purpose: the frontend links to it with a plain
    <a download> tag, which cannot send an Authorization header.
    The data is generated here and contains nothing private.
    """

    rng = np.random.default_rng(42)

    hours = pd.date_range(
        "2025-01-01",
        periods=14 * 24,
        freq="h"
    )

    # Typical household day: low overnight, morning bump, evening peak.
    profile = np.array([
        0.45, 0.42, 0.38, 0.35, 0.33, 0.42, 0.71, 1.10,
        0.90, 0.79, 0.74, 0.82, 0.88, 0.94, 1.13, 1.26,
        1.16, 1.38, 1.48, 1.52, 1.72, 1.61, 1.13, 0.68,
    ])

    energy = profile[hours.hour] * np.where(
        hours.dayofweek >= 5,
        1.12,
        1.0
    )

    energy = energy * rng.normal(1.0, 0.08, len(hours))

    # A few obvious spikes and dips so the anomaly tools have
    # something to find.
    for position, factor in ((60, 3.2), (130, 3.6), (205, 0.1), (290, 3.0)):
        energy[position] *= factor

    frame = pd.DataFrame({
        "Hour": hours.strftime("%Y-%m-%d %H:%M:%S"),
        "Energy_kWh": np.round(np.clip(energy, 0.02, None), 3),
    })

    return Response(
        content=frame.to_csv(index=False),
        media_type="text/csv",
        headers={
            "Content-Disposition":
                'attachment; filename="wattminds_demo.csv"'
        },
    )


# =========================================================
# 14. SERVE THE FRONTEND
# =========================================================

@app.get("/")
def index():
    return FileResponse(
        FRONTEND / "indexwatt.html"
    )


# Static files must be mounted LAST.
# This allows /api/... routes to match first.

app.mount(
    "/",
    StaticFiles(
        directory=str(FRONTEND)
    ),
    name="frontend"
)