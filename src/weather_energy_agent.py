import requests

GEOCODING_URL = "https://geocoding-api.open-meteo.com/v1/search"
WEATHER_URL = "https://api.open-meteo.com/v1/forecast"


def normalize_appliances(appliances):
    if appliances is None:
        return []
    # DataFrame-like inputs used by the original Streamlit version.
    if hasattr(appliances, "columns") and hasattr(appliances, "empty"):
        if appliances.empty:
            return []
        if "Appliance" not in appliances.columns:
            raise ValueError("Appliance data must have an 'Appliance' column.")
        values = appliances["Appliance"].tolist()
    elif isinstance(appliances, (list, tuple, set)):
        values = list(appliances)
    elif isinstance(appliances, str):
        values = [appliances]
    else:
        raise ValueError("Appliances must be a list of names or a DataFrame.")
    names = []
    for item in values:
        if isinstance(item, dict):
            item = item.get("Appliance", item.get("name", ""))
        name = str(item).strip().lower()
        if name and name not in ("none", "nan"):
            names.append(name)
    return names


def get_weather_energy_advice(city, appliances=None, tariff=8.0):
    """Fetch current weather and return contextual advisory recommendations."""
    if not isinstance(city, str) or not city.strip():
        raise ValueError("Please enter a city name.")
    appliance_names = normalize_appliances(appliances)

    try:
        geo_response = requests.get(GEOCODING_URL, params={
            "name": city.strip(), "count": 1, "language": "en", "format": "json"
        }, timeout=15)
        geo_response.raise_for_status()
        locations = geo_response.json().get("results") or []
        if not locations:
            raise ValueError(f"Could not find city '{city}'. Check the spelling.")
        location = locations[0]

        weather_response = requests.get(WEATHER_URL, params={
            "latitude": location["latitude"],
            "longitude": location["longitude"],
            "current": "temperature_2m,relative_humidity_2m,is_day,weather_code",
            "daily": "sunrise,sunset",
            "timezone": "auto",
            "forecast_days": 1,
        }, timeout=20)
        weather_response.raise_for_status()
        weather = weather_response.json()
    except requests.RequestException as exc:
        raise ValueError("Weather service is unavailable. Check your internet connection and try again.") from exc

    current = weather.get("current") or {}
    daily = weather.get("daily") or {}
    temperature = current.get("temperature_2m")
    humidity = current.get("relative_humidity_2m")
    is_day = current.get("is_day")
    if temperature is None or is_day is None:
        raise ValueError("Current weather data is incomplete.")
    temperature = float(temperature)
    is_day = bool(int(is_day))

    has_ac = any(name == "ac" or "air conditioner" in name or "air conditioning" in name or "a/c" in name for name in appliance_names)
    has_fan = any("fan" in name for name in appliance_names)
    has_lights = any(any(word in name for word in ("light", "bulb", "lamp")) for name in appliance_names)
    alerts = []

    if has_ac:
        if temperature <= 22:
            alerts.append({"Priority": "Review", "Title": "Cool outdoor conditions",
                           "Reason": f"Outdoor temperature is {temperature:.1f}°C. Check indoor comfort before running AC.",
                           "Action": "If already comfortable, consider raising the AC setpoint or reducing usage."})
        elif temperature >= 32:
            alerts.append({"Priority": "High", "Title": "Hot-weather AC guidance",
                           "Reason": f"Outdoor temperature is {temperature:.1f}°C. Cooling demand may be higher.",
                           "Action": "Close doors and windows during cooling, use a comfortable setpoint, and maintain filters."})
        else:
            alerts.append({"Priority": "Normal", "Title": "AC efficiency check",
                           "Reason": f"Outdoor temperature is {temperature:.1f}°C; indoor comfort may differ.",
                           "Action": "Check indoor comfort and use an efficient AC setting."})

    if has_fan:
        if temperature <= 24:
            alerts.append({"Priority": "Review", "Title": "Fan usage review",
                           "Reason": "Outdoor conditions are relatively cool, though indoors may differ.",
                           "Action": "Turn the fan off when it is not needed for comfort."})
        else:
            alerts.append({"Priority": "Normal", "Title": "Fan comfort check",
                           "Reason": f"Outdoor temperature is {temperature:.1f}°C.",
                           "Action": "Use fans when helpful and switch them off in unoccupied rooms."})

    if has_lights and is_day:
        alerts.append({"Priority": "Review", "Title": "Daylight opportunity",
                       "Reason": "It is daytime; indoor natural light may be sufficient.",
                       "Action": "Switch off unnecessary lights if the room is bright enough."})

    if not alerts:
        alerts.append({"Priority": "Normal", "Title": "General energy-saving check",
                       "Reason": "No matching AC, fan, or lighting appliance generated a specific alert.",
                       "Action": "Review any appliances running unnecessarily and switch them off when appropriate."})

    sunrise = daily.get("sunrise") or []
    sunset = daily.get("sunset") or []
    return {
        "city": location["name"],
        "country": location.get("country", ""),
        "temperature_c": temperature,
        "humidity_percent": humidity,
        "is_day": is_day,
        "local_time": current.get("time", ""),
        "sunrise": sunrise[0] if sunrise else None,
        "sunset": sunset[0] if sunset else None,
        "alerts": alerts,
    }