# Debug Scripts for Wunderground Scraper

This directory contains debugging tools to help troubleshoot issues with the Wunderground scraper integration.

## Quick Start

```bash
# Install dependencies
cd debug
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt

# Test sensor availability
python test_sensors.py https://your-pws-url

# Find/validate station URLs
python find_stations.py "Your City, State"
```

## Scripts

### 🧪 test_sensors.py

Tests all sensors for a given weather station and shows which ones are available.

**Usage:**
```bash
python test_sensors.py [URL]
```

**Features:**
- Tests all 15 sensor types (temperature, humidity, UV, solar, etc.)
- Shows time-based availability (UV/Solar only during day)
- Exports results to JSON file
- Color-coded output for easy debugging

**Example:**
```bash
python test_sensors.py https://www.wunderground.com/dashboard/pws/KNYNEWYO1959
```

**Output:**
```
🌦️  Testing Weather Station: https://www.wunderground.com/dashboard/pws/KNYNEWYO1959
📅 Test Time: 2025-09-17 22:30:15 EDT

📊 SENSOR AVAILABILITY REPORT
--------------------------------------------------

🌡️  Temperature Sensors:
  ✅ temperature               : 63
  ✅ feels_like               : 63
  ✅ dew_point                : 59

💨 Wind Sensors:
  ✅ wind_speed               : 0
  ❌ wind_gust                : Not available
  ❌ wind_direction           : Not available

📈 SUMMARY:
  Available: 8/15 sensors
  Success Rate: 53.3%
  🌙 Nighttime test - UV/Solar sensors not expected
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

### ❌ UV Index or Solar Radiation Missing

**Possible Causes:**
1. **Time of day**: These sensors only report during daylight (6 AM - 6 PM typically)
2. **Station capability**: Not all PWS have UV/solar sensors
3. **Weather conditions**: May not report during overcast conditions

**Debug Steps:**
1. Test during midday hours (10 AM - 4 PM)
2. Check if the station specs mention UV/solar sensors
3. Try a different weather station

### ❌ Wind Direction Missing

**Possible Causes:**
1. Station doesn't have wind vane (direction sensor)
2. Wind speed is 0 (calm conditions)
3. Different HTML structure on some stations

**Debug Steps:**
1. Check during windy conditions
2. Look for compass/direction elements on the web page
3. Try alternative stations

### ❌ No Sensors Found

**Possible Causes:**
1. Incorrect URL format
2. Station offline or not reporting
3. Wunderground page structure changed

**Debug Steps:**
1. Validate URL with `find_stations.py`
2. Check if station page loads in browser
3. Try alternative URL formats

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