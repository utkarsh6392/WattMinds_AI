# WattMinds 2.0
### AI-Powered Energy Analytics & Optimization Platform
https://wattminds-ai.onrender.com

WattMinds 2.0 is a full-stack, AI-powered energy analytics and decision-support platform designed to help users understand electricity consumption, identify unusual energy usage, estimate costs, and explore energy-saving opportunities.

The platform combines a modern, responsive dashboard with a Python FastAPI backend, machine learning utilities, weather-based recommendations, and Supabase authentication.

**Project Status:** Active Development  
**Frontend:** HTML, CSS, Vanilla JavaScript  
**Backend:** Python, FastAPI  
**Authentication:** Supabase Auth  
**Deployment:** Render

---

## Key Features

WattMinds provides nine integrated modules:

| Module | Description |
|---|---|
| Overview | Central dashboard for energy insights and platform navigation |
| Appliance Studio | Analyze appliance-level electricity consumption and estimated costs |
| ML Forecast | Generate energy predictions from uploaded CSV datasets using the configured prediction model |
| Anomaly Center | Identify unusual energy readings and consumption anomalies |
| Weather Advisor | Generate weather-aware energy recommendations |
| Energy Copilot | Ask energy-related questions and receive calculation-based insights and recommendations |
| ML Pattern Lab | Explore unusual consumption patterns using Isolation Forest |
| What-If Simulator | Explore how changes in appliance usage could affect energy consumption and costs |
| Replacement Advisor | Find which appliances are worth replacing, with what, and how much money and energy that saves |

### Authentication

WattMinds uses Supabase Authentication to support:

- Email and password signup
- Secure login
- Email verification, when enabled
- Forgot-password and password-reset flows
- Persistent authentication sessions
- User profile display
- Logout
- Bearer-token verification for protected backend APIs

Authentication is handled through Supabase Auth, while FastAPI verifies access tokens before processing protected requests.

---

## Technology Stack

| Layer | Technologies |
|---|---|
| Frontend | HTML5, CSS3, JavaScript |
| UI Design | Dark Theme, Bento Grid, Glassmorphism |
| Backend | Python, FastAPI, Uvicorn |
| Data Processing | Pandas, NumPy |
| Machine Learning | Scikit-learn, Joblib |
| Authentication | Supabase Auth |
| API Communication | REST APIs, JSON, Fetch API |
| Deployment | Render |
| Version Control | Git, GitHub |

---

## Project Structure

```text
WattMinds/
│
├── backend/
│   └── main.py
│
├── frontend/
│   ├── index.html
│   ├── styles.css
│   ├── app.js
│   └── auth.js
│
├── src/
│   ├── energy_agent.py
│   ├── manual_energy_agent.py
│   ├── weather_energy_agent.py
│   ├── anomaly_detector.py
│   └── replacement_advisor.py
│
├── models/
│   └── final_energy_prediction_model.joblib
│
├── tests/
│   ├── test_replacement_advisor.py
│   └── test_api_replacements.py
│
├── requirements-web.txt
├── .gitignore
├── .env
└── README.md
```

**Note:** The structure above represents the expected application components. The trained model file is required for features that depend on it and may not be included in the GitHub repository.

The `.env` file contains local configuration and must not be committed to GitHub.

---

## Getting Started

### 1. Clone the Repository

```bash
git clone https://github.com/YOUR_USERNAME/YOUR_REPOSITORY.git
cd YOUR_REPOSITORY
```

Replace the placeholders with your actual GitHub username and repository name.

### 2. Create a Virtual Environment

On Windows:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

On macOS/Linux:

```bash
python3 -m venv .venv
source .venv/bin/activate
```

### 3. Install Dependencies

```bash
python -m pip install -r requirements-web.txt
```

The web application requires FastAPI, Uvicorn, Python Multipart, Python Dotenv, Pandas, NumPy, Requests, Joblib, and Scikit-learn.

### 4. Configure Supabase

Create a `.env` file in the project root:

```env
SUPABASE_URL=https://YOUR_PROJECT_ID.supabase.co
SUPABASE_PUBLISHABLE_KEY=YOUR_SUPABASE_PUBLISHABLE_KEY
```

Get the credentials from your Supabase project's settings.

Only use the publishable key in this configuration. Never expose a Supabase secret key or service-role key through a public API.

In Supabase:

1. Open Authentication settings.
2. Enable email authentication.
3. Configure the Site URL.
4. Add the appropriate local and production redirect URLs.

For local development, use:

```text
http://localhost:8000
http://127.0.0.1:8000
```

### 5. Run the Application

From the project root:

```bash
python -m uvicorn backend.main:app --reload --host 127.0.0.1 --port 8000
```

Open:

```text
http://127.0.0.1:8000
```

The application should display the authentication interface. After successful login, users can access the WattMinds dashboard.

---

## API Documentation

FastAPI provides interactive API documentation at:

```text
http://127.0.0.1:8000/docs
```

### Main API Endpoints

| Method | Endpoint | Description |
|---|---|---|
| GET | `/api/health` | Check backend status |
| GET | `/api/public-config` | Retrieve browser-safe Supabase configuration |
| POST | `/api/manual` | Analyze appliance energy usage |
| POST | `/api/forecast` | Generate energy predictions from CSV data |
| POST | `/api/anomalies` | Detect unusual energy readings |
| POST | `/api/weather` | Generate weather-aware energy recommendations |
| POST | `/api/copilot` | Process energy-related questions |
| POST | `/api/ml-patterns` | Detect unusual consumption patterns using machine learning |
| GET | `/api/replacement-types` | Appliance types for the Replacement Advisor dropdown |
| POST | `/api/replacements` | Recommend appliance replacements with savings and payback |

Protected API endpoints require a valid Supabase access token.

Example authorization header:

```http
Authorization: Bearer YOUR_ACCESS_TOKEN
```

---

## CSV Dataset Support

WattMinds supports CSV-based energy analysis.

The backend accepts CSV uploads for compatible forecasting and anomaly-detection features.

For the anomaly detection endpoint, a dataset should contain an `Energy_kWh` column.

Example:

```csv
Energy_kWh
1.25
1.40
1.32
5.90
1.28
```

The backend applies file validation and a maximum upload size of 15 MB.

Different machine learning modules may require additional columns or a particular input structure.

---

## Machine Learning

WattMinds combines existing energy-analysis modules with machine learning techniques.

### Energy Forecasting

Uses the configured trained prediction model to estimate energy consumption from compatible datasets.

### Anomaly Detection

Analyzes energy readings to identify unusual consumption behavior.

### ML Pattern Analysis

Uses Isolation Forest to detect statistical outliers in energy-consumption datasets.

### Energy Recommendations

Provides appliance-level calculations, estimated electricity costs, and potential energy-saving suggestions.

**Important:** Machine learning outputs are estimates and should not be treated as guaranteed electricity savings or utility-billing measurements.

## Replacement Advisor

The Replacement Advisor recommends which of your appliances to replace, with what type of appliance, and shows the energy and money saved and how long the upgrade takes to pay for itself.

**Example output:** "Replace Old tube light (40 W) with LED batten (20 W). You save 0.48 kWh per day, about Rs 1,402 per year. The replacement costs about Rs 1,800 (4 x Rs 450), so it pays for itself in roughly 15.6 months."

### How to use it

1. Open **Replacement Advisor** in the sidebar.
2. Enter your appliances (name, type, watts, hours per day, quantity, optional age), or select **Use my Appliance Studio list** to copy the rows you already entered there.
3. Leave the type on **Auto-detect from name**, or pick it from the list.
4. Set your tariff and select **Find replacements**.
5. Optional: open **Advanced** and enter the watts and price from a real quote.

### Formulas

Per appliance, using **your entered watts** as the old appliance's power:

```text
kwh_saved_per_day      = (old_watts - new_watts) x hours_per_day x quantity / 1000
monthly_saving_rs      = kwh_saved_per_day x 30  x tariff
yearly_saving_rs       = kwh_saved_per_day x 365 x tariff
total_replacement_cost = replacement price x quantity
payback_months         = total_replacement_cost / monthly_saving_rs
```

Priority: **High** = payback under 12 months, **Medium** = 12 to 36 months, **Low** = more than 36 months. An appliance whose wattage is within 10% of the replacement's (or below it) is listed as **already efficient** and is not recommended for replacement. Appliances that cannot be matched to a type, or that are used 0 hours a day, are listed under **Not assessed** with the reason.

### Assumptions

- Rated power for the hours entered, a 30-day month, a 365-day year and a flat tariff.
- Catalog wattages and prices are **indicative estimates for India**, not quotes. Enter real quotes under Advanced for an accurate payback.
- Payback ignores installation charges, resale value, subsidies and price changes.
- For refrigerators and air conditioners the replacement wattage is an average running power, so enter the hours the compressor actually runs, as in Appliance Studio.

### Replacement catalog (typical values)

| Old appliance | Replace with | Typical watts | Typical price (Rs) |
|---|---|---|---|
| Incandescent bulb | LED bulb | 9 W | 100 |
| CFL | LED bulb | 9 W | 100 |
| Tube light (T12 / T8) | LED batten | 20 W | 450 |
| Old ceiling fan | BLDC ceiling fan | 30 W | 3,200 |
| Old non-inverter AC | 5-star inverter AC | 950 W | 42,000 |
| Old refrigerator | 5-star inverter refrigerator | 100 W | 28,000 |
| CRT TV | LED TV | 40 W | 14,000 |
| Old desktop computer | Energy-efficient laptop | 45 W | 45,000 |
| CRT monitor | LED monitor | 20 W | 7,000 |
| Electric water heater (geyser) | 5-star geyser | 1,700 W | 9,000 |
| Old water pump / motor | Energy-efficient pump | 600 W | 12,000 |

To change a price or add an appliance type, edit the `CATALOG` list at the top of `src/replacement_advisor.py`. Nothing else needs to change.

### API

Both endpoints require a valid Supabase access token, like the other analysis endpoints.

- `GET /api/replacement-types` returns `{"types": [...]}` for the dropdown.
- `POST /api/replacements` takes `{"appliances": [{"name", "type_key", "watts", "hours_per_day", "quantity", "age_years", "replacement_watts", "replacement_cost_rs"}], "tariff": 8}` and returns `{"status": "success", "result": {"recommendations", "already_efficient", "not_assessed", "summary", "assumptions"}}`. `type_key`, `age_years` and the two replacement fields are optional.

### Energy Copilot

Questions such as "Which appliance should I replace?" or "Should I buy an LED?" are answered with the same calculation, using the appliance entered in the Copilot form.

### Tests

```bash
python -m pip install httpx      # only needed for the API tests
python -m unittest discover -s tests -v
```

---

## Deployment on Render

WattMinds can be deployed as a single Python Web Service on Render.

### Step 1: Push the Project to GitHub

```bash
git add .
git commit -m "Prepare WattMinds for deployment"
git push
```

### Step 2: Create a Render Web Service

Open [Render Dashboard](https://dashboard.render.com).

Select **New → Web Service** and connect your GitHub repository.

Use the following configuration:

| Setting | Value |
|---|---|
| Runtime | Python |
| Region | Singapore (recommended for users in India) |
| Branch | main |
| Root Directory | Leave blank |
| Build Command | `pip install -r requirements-web.txt` |
| Start Command | `uvicorn backend.main:app --host 0.0.0.0 --port $PORT` |

Select an available instance type appropriate for the application's memory and performance requirements.

### Step 3: Add Environment Variables

In the Render Environment section, configure:

```env
SUPABASE_URL=https://YOUR_PROJECT_ID.supabase.co
SUPABASE_PUBLISHABLE_KEY=YOUR_SUPABASE_PUBLISHABLE_KEY
```

Do not upload your `.env` file to GitHub.

### Step 4: Deploy

Deploy the service and wait for the build and startup process to complete.

After deployment, Render will provide a URL similar to:

```text
https://your-service.onrender.com
```

### Step 5: Update Supabase Redirect URLs

In Supabase Dashboard → Authentication → URL Configuration, set the production Site URL to your actual Render URL.

Add the production URL to the allowed redirect URLs:

```text
https://your-service.onrender.com/**
```

Retain local development redirect URLs if needed.

### Step 6: Verify Deployment

Check the following:

```text
https://your-service.onrender.com/api/health
https://your-service.onrender.com/api/public-config
https://your-service.onrender.com/docs
```

Then test signup, login, dashboard access, API operations, and logout.

**Deployment note:** If the trained machine learning model is excluded from Git through `.gitignore`, it will not automatically be available on Render. Model-dependent features require the model artifact to be supplied through an appropriate deployment mechanism.

---

## Security

The application follows several basic security practices:

- Supabase Auth manages user authentication.
- Protected backend endpoints verify access tokens.
- Environment variables store deployment configuration.
- `.gitignore` excludes local environment files and private keys.
- Uploaded CSV files are validated before processing.
- Backend request models validate input values.

The Supabase publishable key is public by design. Secret keys and service-role keys must never be exposed in frontend code or public configuration endpoints.

Additional security testing, monitoring, and production hardening are recommended before handling sensitive or business-critical data.

---

## Future Enhancements

Potential improvements include:

- Historical energy consumption tracking
- Persistent user-specific analytics
- Smart meter and IoT integration
- Real-time monitoring
- Advanced forecasting models
- Downloadable analytics reports
- Notification and alert systems
- Multi-property energy management
- Personalized energy-saving plans

---

## Contributing

Contributions and suggestions are welcome.

To contribute:

1. Fork the repository.
2. Create a feature branch.
3. Make your changes.
4. Test your changes locally.
5. Open a pull request describing the improvements.

---

## Disclaimer

WattMinds is an energy analytics and decision-support project.

Forecasts, anomaly scores, electricity costs, and savings recommendations depend on the supplied data, model quality, tariff assumptions, and operating conditions. Results should be interpreted as estimates.

---

## License

No license is specified in this README. Refer to the repository's `LICENSE` file, if present, for usage and redistribution permissions.

---

**WattMinds 2.0 — Smarter Energy Insights, Better Decisions.**