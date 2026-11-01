![Wunderground PWS for Home Assistant](logo.png)

# Wunderground PWS - Home Assistant Integration

A Home Assistant integration for fetching weather data from Wunderground Personal Weather Stations.

It talks to the same Weather.com PWS endpoint Wunderground's own site uses, so no paid API
subscription is required — just a station ID.

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

## 🛡️ Reliability

Weather.com's API is not a stable public product, so the integration is built to survive it:

- **Retries transient failures.** A dropped connection, timeout, or 5xx is retried up to 3 times
  with backoff instead of blanking the sensors.
- **Holds the last good reading through short outages.** Sensors keep their last value (with
  `stale: true` as an attribute) for up to 6 consecutive failed polls (~30 minutes at the default
  5-minute interval), then go `unavailable` so a genuinely dead station still surfaces.
- **Rotates API keys.** The public key is shared by every scraper in existence and Weather.com
  throttles it without warning (`401 API key is throttled`). The integration keeps a list of keys
  and moves to the next one when a key is refused.
- **Permanent failures fail fast.** An HTTP 204 (station not reporting) or unusable payload raises
  immediately — retrying cannot fix those.

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

The retry/stale-hold and key-rotation logic are covered by standalone tests that run without Home
Assistant installed:

```bash
python3 debug/test_key_rotation.py  # run from the repo root
python3 debug/test_retry_logic.py   # see the path note at the top of the script
```

See [debug/README.md](debug/README.md) for detailed debugging instructions.

## ❓ FAQ

**Q: Do I need to create an API key?**
A: No. The integration uses the public Weather.com PWS API with keys found in Wunderground's source code. They are shared public keys, so if Weather.com throttles one the integration rotates to the next.

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

### v0.3.5 (2026-10-31)
- Logo subtitle trimmed to `PERSONAL WEATHER STATION DATA`

### v0.3.4 (2026-10-31)
- Repository renamed to `wunderground-scraper`, new logo (no more pirate artwork)

### v0.3.3 (2026-10-31)
- Manifest documentation and issue tracker now point at this GitHub repository
- Restored the README and logo (a previous commit replaced both with unexpanded shell placeholders)

### v0.3.2 (2026-10-31)
- Fixed `extra_state_attributes` raising `AttributeError` for every non-Celsius sensor, which made
  Home Assistant refuse to add 12 of the 15 entities even though the coordinator was fetching fine

### v0.3.1 (2026-10-31)
- API keys are now a list and rotate on `401`/`403`, so one throttled key no longer takes every
  sensor down for days

### v0.3.0 (2026-09-20)
- Survives intermittent Weather.com edge outages: retry on transient faults, hold the last good
  reading up to 6 failed polls with `stale: true`, fail fast on permanent faults

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
*Repository: [github.com/aserper/wunderscraper](https://github.com/aserper/wunderscraper)* 🔗  
*Last Updated: 2026-10-31*
