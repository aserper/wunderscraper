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
3.  Enter the full URL of the Wunderground PWS you want to monitor (e.g., `https://www.wunderground.com/weather/us/ma/newyork/KNYNEWYO1959`).
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
*   🎈 Pressure
*   🌧️ Precipitation Rate
*   🌧️ Precipitation Accumulation

---

*Author: Amit Serper* 👋
*Repository: [github.com/aserper/wunderground-local-haas](https://github.com/aserper/wunderground-local-haas)* 🔗