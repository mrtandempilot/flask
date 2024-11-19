import os
import requests
import json
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def test_api_key():
    api_key = os.getenv('OPENWEATHER_API_KEY')
    print(f"Testing API key: {api_key}")

    # Test 1: Geocoding API
    print("\n1. Testing Geocoding API...")
    geo_url = f"http://api.openweathermap.org/geo/1.0/direct?q=Istanbul&limit=1&appid={api_key}"
    geo_response = requests.get(geo_url)
    
    print(f"Status Code: {geo_response.status_code}")
    if geo_response.status_code == 200:
        print("[PASS] Geocoding API test passed")
        location_data = geo_response.json()
        lat = location_data[0]['lat']
        lon = location_data[0]['lon']
        print(f"Coordinates: {lat}, {lon}")
    else:
        print("[FAIL] Geocoding API test failed")
        print(f"Error: {geo_response.text}")

    # Test 2: Current Weather API
    print("\n2. Testing Current Weather API...")
    weather_url = f"https://api.openweathermap.org/data/2.5/weather?q=Istanbul&units=metric&appid={api_key}"
    weather_response = requests.get(weather_url)
    
    print(f"Status Code: {weather_response.status_code}")
    if weather_response.status_code == 200:
        print("[PASS] Current Weather API test passed")
        weather_data = weather_response.json()
        print(f"Current temperature: {weather_data['main']['temp']}C")
        print(f"Weather condition: {weather_data['weather'][0]['description']}")
    else:
        print("[FAIL] Current Weather API test failed")
        print(f"Error: {weather_response.text}")

    # Test 3: One Call API
    print("\n3. Testing One Call API...")
    if geo_response.status_code == 200:
        onecall_url = f"https://api.openweathermap.org/data/2.5/onecall?lat={lat}&lon={lon}&exclude=minutely,hourly,alerts&units=metric&appid={api_key}"
        onecall_response = requests.get(onecall_url)
        
        print(f"Status Code: {onecall_response.status_code}")
        if onecall_response.status_code == 200:
            print("[PASS] One Call API test passed")
            forecast_data = onecall_response.json()
            print("\nNext 7 days forecast:")
            for day in forecast_data['daily'][:7]:
                from datetime import datetime
                date = datetime.fromtimestamp(day['dt']).strftime('%Y-%m-%d')
                print(f"{date}: {day['temp']['day']}C, {day['weather'][0]['description']}")
        else:
            print("[FAIL] One Call API test failed")
            print(f"Error: {onecall_response.text}")

if __name__ == "__main__":
    test_api_key()
