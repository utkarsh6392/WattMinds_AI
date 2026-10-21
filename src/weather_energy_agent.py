
import requests
from datetime import datetime


GEOCODING_URL = "https://geocoding-api.open-meteo.com/v1/search"
WEATHER_URL = "https://api.open-meteo.com/v1/forecast"


def get_weather_energy_advice(city, appliances=None, tariff=8.0):
    """
    Fetch current local weather and generate energy-saving advice.
    This creates recommendations only; it does not control appliances.
    """

    if not city or not city.strip():
        raise ValueError("Please enter a city name.")

    # Tool 1: Find city coordinates.
    geo_response = requests.get(
        GEOCODING_URL,
        params={
            "name": city.strip(),
            "count": 1,
            "language": "en",
            "format": "json",
        },
        timeout=15,
    )
    geo_response.raise_for_status()
    geo_data = geo_response.json()

    locations = geo_data.get("results", [])

    if not locations:
        raise ValueError(
            f"Could not find city '{city}'. Check the spelling."
        )

    location = locations[0]
    latitude = location["latitude"]
    longitude = location["longitude"]
    city_name = location["name"]
    country = location.get("country", "")

    # Tool 2: Fetch current weather and today's sunrise/sunset.
    weather_response = requests.get(
        WEATHER_URL,
        params={
            "latitude": latitude,
            "longitude": longitude,
            "current": (
                "temperature_2m,relative_humidity_2m,"
                "is_day,weather_code"
            ),
            "daily": "sunrise,sunset",
            "timezone": "auto",
            "forecast_days": 1,
        },
        timeout=20,
    )
    weather_response.raise_for_status()
    weather = weather_response.json()

    current = weather.get("current", {})
    daily = weather.get("daily", {})

    temperature = current.get("temperature_2m")
    humidity = current.get("relative_humidity_2m")
    is_day = current.get("is_day")
    local_time = current.get("time", "")

    if temperature is None or is_day is None:
        raise ValueError("Current weather data is incomplete.")

    # Appliance details can optionally personalize recommendations.
    appliance_names = []

    if appliances is not None and not appliances.empty:
        appliance_names = [
            str(name).strip().lower()
            for name in appliances["Appliance"].tolist()
        ]

    has_ac = any(
        "ac" in name
        or "air conditioner" in name
        for name in appliance_names
    )

    has_fan = any(
        "fan" in name
        for name in appliance_names
    )

    has_lights = any(
        "light" in name
        or "bulb" in name
        or "lamp" in name
        for name in appliance_names
    )

    alerts = []

    # Rule 1: Weather-aware AC guidance.
    if has_ac:
        if temperature <= 22:
            alerts.append({
                "Priority": "Review",
                "Title": "Cool outdoor conditions",
                "Reason": (
                    f"Outdoor temperature is {temperature:.1f}°C. "
                    "Check indoor temperature and comfort before "
                    "running the AC."
                ),
                "Action": (
                    "If the room is already comfortable, consider "
                    "raising the AC setpoint or reducing its usage."
                ),
            })

        elif temperature >= 32:
            alerts.append({
                "Priority": "High",
                "Title": "Hot-weather AC guidance",
                "Reason": (
                    f"Outdoor temperature is {temperature:.1f}°C. "
                    "Cooling demand may be higher."
                ),
                "Action": (
                    "Keep doors and windows closed while cooling, "
                    "use a comfortable setpoint, and clean filters "
                    "according to the manufacturer's instructions."
                ),
            })

        else:
            alerts.append({
                "Priority": "Normal",
                "Title": "AC efficiency check",
                "Reason": (
                    f"Outdoor temperature is {temperature:.1f}°C. "
                    "Outdoor temperature alone cannot confirm "
                    "whether indoor cooling is needed."
                ),
                "Action": (
                    "Check indoor comfort and use an efficient "
                    "temperature setting."
                ),
            })

    # Rule 2: Fan guidance.
    if has_fan:
        if temperature <= 24:
            alerts.append({
                "Priority": "Review",
                "Title": "Fan usage review",
                "Reason": (
                    "Outdoor conditions are relatively cool, "
                    "but indoor conditions may differ."
                ),
                "Action": (
                    "If the room feels comfortable without the fan, "
                    "consider switching it off when not needed."
                ),
            })
        else:
            alerts.append({
                "Priority": "Normal",
                "Title": "Fan comfort check",
                "Reason": (
                    f"Outdoor temperature is {temperature:.1f}°C."
                ),
                "Action": (
                    "Use the fan when it improves comfort; "
                    "turn it off when the room is unoccupied."
                ),
            })

    # Rule 3: Daylight-aware lighting guidance.
    if has_lights and int(is_day) == 1:
        alerts.append({
            "Priority": "Review",
            "Title": "Daylight opportunity",
            "Reason": (
                "It is currently daytime in the selected location. "
                "This does not guarantee sufficient indoor daylight."
            ),
            "Action": (
                "If the room is bright enough, switch off "
                "unnecessary lights."
            ),
        })

    # General recommendation when no matching appliance is entered.
    if not alerts:
        alerts.append({
            "Priority": "Normal",
            "Title": "General energy-saving check",
            "Reason": (
                "No matching AC, fan, or lighting appliance "
                "was identified in the supplied appliance list."
            ),
            "Action": (
                "Review appliances that are running unnecessarily "
                "and switch them off when safe and appropriate."
            ),
        })

    return {
        "city": city_name,
        "country": country,
        "temperature_c": float(temperature),
        "humidity_percent": humidity,
        "is_day": bool(int(is_day)),
        "local_time": local_time,
        "sunrise": (
            daily.get("sunrise", [None])[0]
        ),
        "sunset": (
            daily.get("sunset", [None])[0]
        ),
        "alerts": alerts,
    }
