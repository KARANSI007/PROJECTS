import requests

API_KEY = "e317fe0eef75af311e71d3eb0d3118d1"  # replace with your key
CITY = "Mumbai" 
URL = f"http://api.openweathermap.org/data/2.5/weather?q={CITY}&appid={API_KEY}&units=metric"

response = requests.get(URL)

if response.status_code == 200:
    data = response.json()
    city = data["name"]
    country = data["sys"]["country"]
    temp = data["main"]["temp"]
    feels_like = data["main"]["feels_like"]
    humidity = data["main"]["humidity"]
    weather = data["weather"][0]["description"]

    print(f"📍 {city}, {country}")
    print(f"🌡️ Temperature: {temp}°C (Feels like {feels_like}°C)")
    print(f"💧 Humidity: {humidity}%")
    print(f"☁️ Condition: {weather}")
else:
    print("❌ Error fetching data:", response.status_code)
