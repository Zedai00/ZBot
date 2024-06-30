import os

import requests


def handle_res(params):
    city = params[0]
    api_key = os.getenv("WEATHER_API")
    url = f"http://api.openweathermap.org/data/2.5/weather?q={city}&appid={api_key}&units=metric"
    res = requests.get(url).json()
    if res.get("cod") != 200:
        return {"error": res.get("message", "Error fetching weather data.")}
    weather = res["weather"][0]["description"]
    temperature = res["main"]["temp"]
    humidity = res["main"]["humidity"]
    wind_speed = res["wind"]["speed"]
    weather_info = (
        f"Current weather in {city}: {weather}. "
        f"Temperature: {temperature}°C, "
        f"Humidity: {humidity}%, "
        f"Wind Speed: {wind_speed} m/s."
    )
    return {"weather_info": weather_info}
