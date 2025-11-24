#!/usr/bin/env python3
"""
Debug script to test sensor availability from a Wunderground PWS station.
Usage: python debug/test_sensors.py [URL or Station ID]
"""
import sys
import requests
from datetime import datetime
import json
import re

# Public API key from Wunderground's website source
API_KEY = "e1f10a1e78da46f5b10a1e78da96f525"
API_ENDPOINT = "https://api.weather.com/v2/pws/observations/current"


def extract_station_id(url):
    """Extract station ID from Wunderground URL or return as-is if already an ID."""
    # Match pattern like: /pws/STATIONID
    match = re.search(r'/pws/([A-Z0-9]+)', url)
    if match:
        return match.group(1)
    
    # If it's just a station ID
    if re.match(r'^[A-Z0-9]+$', url):
        return url
    
    return None


def fahrenheit_to_celsius(fahrenheit):
    """Convert Fahrenheit to Celsius."""
    if fahrenheit is None:
        return None

    try:
        celsius = (float(fahrenheit) - 32) * 5 / 9
        return f"{celsius:.1f}"
    except (ValueError, TypeError):
        return None


def test_weather_station(url_or_id):
    """Test all sensors for a given weather station using the API."""
    print(f"🌦️  Testing Weather Station: {url_or_id}")
    print(f"📅 Test Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 80)

    # Extract station ID
    station_id = extract_station_id(url_or_id)
    
    if not station_id:
        print(f"❌ Could not extract station ID from: {url_or_id}")
        print(f"   Please provide a valid Wunderground URL or station ID")
        return False
    
    print(f"📍 Station ID: {station_id}")
    
    try:
        # Build API request
        params = {
            'apiKey': API_KEY,
            'stationId': station_id,
            'format': 'json',
            'units': 'e',
            'numericPrecision': 'decimal'
        }
        
        print(f"🔗 API Endpoint: {API_ENDPOINT}")
        
        # Make API request
        response = requests.get(API_ENDPOINT, params=params, timeout=10)
        
        if response.status_code == 204:
            print(f"❌ Station {station_id} is not reporting data (HTTP 204)")
            print(f"   The station may be offline or doesn't exist")
            return False
        
        response.raise_for_status()
        api_data = response.json()
        
        # Extract observation data
        if not api_data.get('observations') or len(api_data['observations']) == 0:
            print(f"❌ No observations data returned for station {station_id}")
            return False
        
        obs = api_data['observations'][0]
        imperial = obs.get('imperial', {})
        
        print(f"📌 Location: {obs.get('neighborhood', 'Unknown')}")
        print(f"🕐 Last Update: {obs.get('obsTimeLocal', 'Unknown')}")
        print(f"🌍 Coordinates: {obs.get('lat')}°, {obs.get('lon')}°")
        
        # Map API data to sensors
        sensors = {}
        
        # Temperature sensors
        if imperial.get('temp') is not None:
            sensors['temperature'] = str(imperial['temp'])
        
        feels_like = imperial.get('heatIndex') or imperial.get('windChill')
        if feels_like is not None:
            sensors['feels_like'] = str(feels_like)
        
        if imperial.get('dewpt') is not None:
            sensors['dew_point'] = str(imperial['dewpt'])
        
        # Other sensors
        if obs.get('humidity') is not None:
            sensors['humidity'] = str(obs['humidity'])
        
        if imperial.get('pressure') is not None:
            sensors['pressure'] = str(imperial['pressure'])
        
        if imperial.get('windSpeed') is not None:
            sensors['wind_speed'] = str(imperial['windSpeed'])
        
        if imperial.get('windGust') is not None:
            sensors['wind_gust'] = str(imperial['windGust'])
        
        if obs.get('winddir') is not None:
            sensors['wind_direction'] = str(obs['winddir'])
        
        if imperial.get('precipRate') is not None:
            sensors['precipitation_rate'] = str(imperial['precipRate'])
        
        if imperial.get('precipTotal') is not None:
            sensors['precipitation_accumulation'] = str(imperial['precipTotal'])
        
        if obs.get('solarRadiation') is not None:
            sensors['solar_radiation'] = str(obs['solarRadiation'])
        
        if obs.get('uv') is not None:
            sensors['uv_index'] = str(obs['uv'])

        # Print results
        print("\n📊 SENSOR AVAILABILITY REPORT")
        print("-" * 50)

        available_count = 0
        total_count = 0

        # Temperature sensors that need Celsius conversion
        temp_sensors = ['temperature', 'feels_like', 'dew_point']

        sensor_categories = {
            "🌡️  Temperature Sensors": temp_sensors,
            "💨 Wind Sensors": ['wind_speed', 'wind_gust', 'wind_direction'],
            "💧 Moisture Sensors": ['humidity', 'precipitation_accumulation', 'precipitation_rate'],
            "🌫️  Atmospheric Sensors": ['pressure'],
            "☀️  Solar Sensors": ['uv_index', 'solar_radiation']
        }

        for category, sensor_list in sensor_categories.items():
            print(f"\n{category}:")
            for sensor in sensor_list:
                total_count += 1
                if sensor in sensors and sensors[sensor] is not None:
                    available_count += 1
                    value = sensors[sensor]

                    # Show both F and C for temperature sensors
                    if sensor in temp_sensors:
                        celsius_value = fahrenheit_to_celsius(float(value))
                        if celsius_value:
                            print(f"  ✅ {sensor:<25}: {value}°F ({celsius_value}°C)")
                        else:
                            print(f"  ✅ {sensor:<25}: {value}°F")
                    else:
                        print(f"  ✅ {sensor:<25}: {value}")
                else:
                    print(f"  ❌ {sensor:<25}: Not available")

        print(f"\n📈 SUMMARY:")
        print(f"  Available: {available_count}/{total_count} sensors")
        print(f"  Success Rate: {available_count/total_count*100:.1f}%")

        # Time-based recommendations
        current_hour = datetime.now().hour
        if 6 <= current_hour <= 18:
            print(f"  ☀️  Daytime test - UV/Solar sensors should be available if supported")
        else:
            print(f"  🌙 Nighttime test - UV/Solar sensors expected to be 0")

        # Export data
        export_data = {
            'timestamp': datetime.now().isoformat(),
            'station_id': station_id,
            'neighborhood': obs.get('neighborhood'),
            'sensors': {k: v for k, v in sensors.items() if v is not None},
            'available_count': available_count,
            'total_count': total_count,
            'api_response': api_data
        }

        with open('sensor_test_results.json', 'w') as f:
            json.dump(export_data, f, indent=2)

        print(f"\n💾 Results saved to: sensor_test_results.json")

    except requests.exceptions.RequestException as e:
        print(f"❌ Network Error: {e}")
        return False
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False

    return True


if __name__ == "__main__":
    if len(sys.argv) > 1:
        url_or_id = sys.argv[1]
    else:
        # Default test station with good data
        url_or_id = "KTXHOUST4430"
        print("No URL/ID provided, using default test station\n")

    test_weather_station(url_or_id)