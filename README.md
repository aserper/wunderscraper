# Wunderground PWS - Home Assistant Integration

A Home Assistant integration for fetching weather data from Wunderground Personal Weather Stations.

## Installation

1. Copy the `wunderground_scraper` directory to your Home Assistant `custom_components` directory
2. Restart Home Assistant
3. Go to Settings > Devices & Services
4. Click Add Integration and search for "Wunderground Scraper"
5. Enter a station URL (e.g., `https://www.wunderground.com/dashboard/pws/KTXHOUST4430`) or just the station ID (`KTXHOUST4430`)

## 📊 Available Sensors

The integration creates sensors for weather data available from your station:

### Temperature & Humidity
*   🌡️ **Temperature** - Current temperature (°F and °C)
*   🌡️ **Feels Like** - Apparent temperature (accounts for wind chill/heat index)
*   💧 **Dew Point** - Dew point temperature (°F and °C)
*   💧 **Humidity** - Relative humidity percentage

### Wind
*   💨 **Wind Speed** - Current wind speed (mph)
*   💨 **Wind Gust** - Wind gust speed (mph)
*   💨 **Wind Direction** - Wind direction (degrees 0-360)

### Pressure & Precipitation
*   🎈 **Pressure** - Barometric pressure (inHg)
*   🌧️ **Precipitation Rate** - Current rain rate (in/hr)
*   🌧️ **Precipitation Accumulation** - Total daily rainfall (in)

### Solar & UV
*   ☀️ **Solar Radiation** - Solar radiation intensity (W/m²)
*   ☀️ **UV Index** - UV index

**Note:** Not all stations report all sensors. The integration automatically creates only the sensors that have data available. UV and Solar are typically 0 at night.

## 🧪 Testing & Debugging

Before adding to Home Assistant, test your station with the debug script:

```bash
cd debug
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Test with station ID
python test_sensors.py KTXHOUST4430

# Or with full URL
python test_sensors.py https://www.wunderground.com/dashboard/pws/KTXHOUST4430
```

The debug script will show:
- ✅ All available sensors for your station
- 🕐 Last update time
- 📍 Station location
- 📊 Success rate and data completeness

See [debug/README.md](debug/README.md) for detailed debugging instructions.

## ❓ FAQ

**Q: Do I need to create an API key?**
A: No! The integration uses the public Weather.com PWS API with a key found in Wunderground's source code.

**Q: Can I monitor a station I don't own?**
A: Yes! You can monitor any public PWS on Wunderground.

**Q: Why are some sensors showing "0" or "unavailable"?**
A: This depends on your station:
- UV Index & Solar Radiation are 0 at night (normal)
- Some stations don't have all sensors installed
- Check the debug script output to see what's available

**Q: Is my data sent to anyone?**
A: The integration only fetches data from Weather.com (same source Wunderground uses)

## 🔄 Version History

### v0.2.0 (2025-11-23)
- **Complete rewrite** to use Weather.com PWS API instead of HTML scraping
- ✅ 100% sensor success rate (vs ~50% with HTML scraping)
- Faster and more reliable data fetching
- Removed BeautifulSoup4 dependency
- Better error handling and logging
- Automatic station ID extraction from URLs

### v0.1.0
- Initial release with HTML scraping

## 📝 License

This integration is provided as-is for personal use.

---

*Author: Amit Serper* 👋  
*Repository: [github.com/aserper/wunderground-local-haas](https://github.com/aserper/wunderground-local-haas)* 🔗  
*Last Updated: 2025-11-23*