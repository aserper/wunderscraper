# Debug Scripts for Wunderground Scraper

This directory contains debugging tools to help troubleshoot issues with the Wunderground scraper integration.

## Quick Start

```bash
# Install dependencies
cd debug
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt

# Test sensor availability (URL or Station ID)
python test_sensors.py https://www.wunderground.com/dashboard/pws/KTXHOUST4430
# or
python test_sensors.py KTXHOUST4430

# Find/validate station URLs
python find_stations.py "Your City, State"
```

## Scripts

### 🧪 test_sensors.py

Tests all sensors for a given weather station using the Weather.com PWS API.

**Usage:**
```bash
python test_sensors.py [URL or Station ID]
```

**Features:**
- Uses Weather.com PWS API (same as the integration)
- Tests all 12 sensor types (temperature, humidity, UV, solar, etc.)
- Shows both Fahrenheit and Celsius temperatures
- Shows time-based availability (UV/Solar at 0 during night)
- Exports results to JSON file with full API response
- Color-coded output for easy debugging

**Example:**
```bash
# Using full URL
python test_sensors.py https://www.wunderground.com/dashboard/pws/KTXHOUST4430

# Using just station ID
python test_sensors.py KTXHOUST4430
```

**Output:**
```
🌦️  Testing Weather Station: KTXHOUST4430
📅 Test Time: 2025-11-23 20:09:42
================================================================================
📍 Station ID: KTXHOUST4430
🔗 API Endpoint: https://api.weather.com/v2/pws/observations/current
📌 Location: Downtown
🕐 Last Update: 2025-11-23 19:08:00

📊 SENSOR AVAILABILITY REPORT
--------------------------------------------------

🌡️  Temperature Sensors:
  ✅ temperature              : 70.3°F (21.3°C)
  ✅ feels_like               : 70.3°F (21.3°C)
  ✅ dew_point                : 60.0°F (15.6°C)

💨 Wind Sensors:
  ✅ wind_speed               : 5.8
  ✅ wind_gust                : 8.1
  ✅ wind_direction           : 76

📈 SUMMARY:
  Available: 12/12 sensors
  Success Rate: 100.0%
  🌙 Nighttime test - UV/Solar sensors expected to be 0
```

### 🔍 find_stations.py

Helps find and validate Personal Weather Station URLs.

**Usage:**
```bash
# Search for stations by location
python find_stations.py "Boston, MA"

# Validate a specific PWS URL
python find_stations.py https://www.wunderground.com/dashboard/pws/KMABOSTO123
```

**Features:**
- Validates URL format and accessibility
- Suggests alternative URL formats
- Extracts station IDs
- Provides manual search guidance

**Example:**
```bash
python find_stations.py https://www.wunderground.com/dashboard/pws/KNYNEWYO1959

🔍 Validating PWS URL: https://www.wunderground.com/dashboard/pws/KNYNEWYO1959
✅ URL format looks valid
✅ URL is accessible
✅ Weather data found (Temperature: 63)
```

## Common Issues & Solutions

### ❌ Station Returns HTTP 204 (No Content)

**Possible Causes:**
1. Station is offline or not reporting
2. Station ID doesn't exist
3. Station was recently removed

**Debug Steps:**
1. Verify the station exists by visiting the Wunderground URL in a browser
2. Try a different nearby station
3. Check if the station has been updated recently on Wunderground

### ⚠️  Some Sensors Return Null/None

**Possible Causes:**
1. **UV/Solar**: Only available during daylight hours with clear skies
2. **Wind Direction**: May not report when wind speed is 0
3. **Precipitation**: May not report when not raining
4. **Station Equipment**: Not all stations have all sensors

**What's Normal:**
- UV Index and Solar Radiation are 0.0 at night (not null)
- Wind direction may be null during calm conditions
- Some stations only report basic metrics (temp, humidity, pressure)

### ❌ "Could not extract station ID from URL"

**Possible Causes:**
1. Incorrect URL format
2. URL doesn't contain `/pws/STATIONID`

**Solution:**
Use one of these formats:
- Full URL: `https://www.wunderground.com/dashboard/pws/KTXHOUST4430`
- Station ID only: `KTXHOUST4430`

## Files Generated

- `sensor_test_results.json`: Latest test results with timestamps
- Debug logs and error traces

## Integration with Home Assistant

After debugging:

1. **Copy working URLs** from test results
2. **Note available sensors** to set expectations
3. **Test at different times** to understand sensor availability patterns
4. **Update integration config** with validated URLs

## Contributing Debug Info

When reporting issues, please include:

1. Output from `test_sensors.py`
2. Station URL being tested
3. Time of day when tested
4. Expected vs actual sensor availability

This helps maintain and improve the scraper integration.