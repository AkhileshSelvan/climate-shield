import requests
from datetime import date, timedelta


def get_rainfall_data(latitude: float, longitude: float, days: int = 14):
    """
    Fetch recent daily rainfall data from Open-Meteo for the given coordinates.
    Returns total rainfall over the requested window plus daily breakdown.
    """
    end_date = date.today()
    start_date = end_date - timedelta(days=days)

    url = "https://archive-api.open-meteo.com/v1/archive"
    params = {
        "latitude": latitude,
        "longitude": longitude,
        "start_date": start_date.isoformat(),
        "end_date": end_date.isoformat(),
        "daily": "precipitation_sum",
        "timezone": "auto",
    }

    response = requests.get(url, params=params, timeout=10)
    response.raise_for_status()
    data = response.json()

    daily_rainfall = data.get("daily", {}).get("precipitation_sum", [])
    dates = data.get("daily", {}).get("time", [])

    total_rainfall = sum(v for v in daily_rainfall if v is not None)

    return {
        "start_date": start_date.isoformat(),
        "end_date": end_date.isoformat(),
        "days": days,
        "total_rainfall_mm": round(total_rainfall, 2),
        "daily_breakdown": list(zip(dates, daily_rainfall)),
    }
