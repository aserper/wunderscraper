# 🌦️ Wunderground Local Scraper - Home Assistant Integration 🏠

[![hacs_badge](https://img.shields.io/badge/HACS-Default-orange.svg)](https://github.com/hacs/integration)

This is a simple but effective Home Assistant integration that scrapes weather data from a specific Wunderground Personal Weather Station (PWS) page. 📡

It provides local weather data directly from a source you choose, without needing an API key. Just point it at a station URL, and it will create sensor entities for all the key metrics. ✨

## 🚀 Installation

1.  **Copy the Integration Files:**
    Copy the `wunderground_scraper` directory from this repository into your Home Assistant `custom_components` directory.

2.  **Restart Home Assistant:**
    Restart your Home Assistant instance to allow it to detect the new integration.

## ⚙️ Configuration

1.  Go to **Settings > Devices & Services**.
2.  Click **Add Integration** and search for **Wunderground Scraper**.
3.  Enter the full URL of the Wunderground PWS you want to monitor (e.g., `https://www.wunderground.com/weather/us/ma/wellesley/KMAWELLE41`).
4.  Click **Submit**.

The integration will automatically create all available sensors. ✅

## 📊 Available Sensors

The following sensors will be created:

*   🌡️ Temperature
*   🌡️ Feels Like Temperature
*   💧 Dew Point
*   💧 Humidity
*   💨 Wind Speed
*   💨 Wind Gust
*   💨 Wind Direction
*   🎈 Pressure
*   🌧️ Precipitation Rate
*   🌧️ Precipitation Accumulation
*   🌫️ Visibility
*   ☁️ Sky Condition (Clouds)
*   ❄️ Snow Depth
*   ☀️ UV Index*
*   ☀️ Solar Radiation*

*\* UV Index and Solar Radiation are only available during daylight hours and require stations with these sensors.*

## 🐛 Debugging & Troubleshooting

If sensors are missing or not working correctly, use the included debug scripts:

```bash
cd debug
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Test your weather station
python test_sensors.py https://your-pws-url-here

# Find/validate station URLs
python find_stations.py "Your City, State"
```

See [debug/README.md](debug/README.md) for detailed debugging instructions.

---

*Author: Amit Serper* 👋
*Repository: [github.com/aserper/wunderground-local-haas](https://github.com/aserper/wunderground-local-haas)* 🔗