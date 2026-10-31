# Changelog

## [0.3.1] - 2026-10-31

### Fixed - Throttled API key blanked every sensor

Weather.com started answering the hardcoded public key with
`401 API key is throttled`. That is neither a transient fault nor a silent
station, so it went down the `UpdateFailed` path: cache cleared, no retry, and
all 15 sensors sat `unavailable` from 2026-10-21 onward.

- `API_KEYS` is now a list. On `401`/`403` the coordinator rotates to the next
  key and only fails once every key has been refused, so one throttled key no
  longer takes the integration down for days.
- First key replaced with a currently working Weather.com public key; the old
  key is kept as a fallback.
- `debug/test_key_rotation.py` covers rotation, all-keys-refused, and the
  HTTP 204 path (runs with no Home Assistant installed).

## [0.3.0] - 2026-09-20

### Fixed - Survive intermittent Weather.com API outages

The Weather.com edge (`api.weather.com`, Fastly-fronted) intermittently accepts
no TCP connection at all. Measured from this network: roughly 1 in 4 requests
stalled with `conn=0` until timeout, while `www.wunderground.com` and other
Fastly-fronted hosts were unaffected.

Previously a single failed poll marked all 15 sensors unavailable, so a ~25%
upstream failure rate blanked the whole integration in the dashboard and in
recorder history. On 2026-09-20 this produced 27 outages in 167 polls, each
blinking every entity to `unavailable`.

**1. Retry transient failures**

- New `fetch_with_retry()` retries connection/timeout/5xx faults up to 3
  attempts with linear backoff (3s, 6s).
- Failures that retrying cannot fix (HTTP 204 station-silent, unusable payload)
  are raised immediately without retrying.

**2. Hold the last reading through short outages**

- The coordinator caches the last successful reading and serves it while polls
  fail, so brief upstream blips no longer create gaps in history.
- After `MAX_CONSECUTIVE_FAILURES` (6 polls, 30 minutes at the default 5 minute
  interval) it stops serving the stale reading and raises, so a genuinely dead
  station still surfaces as unavailable.
- A permanently silent station (HTTP 204) clears the cache rather than serving
  stale values.
- Sensors now derive availability from the presence of their own value in
  `coordinator.data` rather than `coordinator.last_update_success`, so they stay
  available while a held reading is being served.
- While serving a held reading, sensors expose `stale: true` so consumers can
  tell a cached value from a fresh one.

**3. Metadata fixes**

- `manifest.json` `documentation` and `issue_tracker` pointed at
  `github.com/aserper/wunderground-local-haas`, which returns 404. Now points at
  the real repository.

### Testing

`debug/test_retry_logic.py` runs without Home Assistant by stubbing the two HA
modules the coordinator imports. Covers station ID extraction, Celsius
conversion, retry-on-transient, no-retry-on-permanent, attempt exhaustion, the
stale-hold window, give-up-after-max-failures, and 204 handling.

```bash
python3 debug/test_retry_logic.py
```

## [0.2.0] - 2025-11-23

### Changed - Major Rewrite to Use API Instead of Web Scraping

#### Why the Change?
Wunderground completely redesigned their website, breaking the HTML-based scraper:
- Old CSS selectors (`.wu-value`, `.wu-value-to`, etc.) no longer exist
- Weather data is now embedded in JavaScript, not HTML elements
- The website uses Weather.com's PWS API internally

#### What Changed?

**1. Switched from HTML Scraping to Direct API Access**
- Now uses Weather.com PWS API: `https://api.weather.com/v2/pws/observations/current`
- Uses public API key found in Wunderground's website source: `e1f10a1e78da46f5b10a1e78da96f525`
- No more BeautifulSoup4 dependency
- Faster and more reliable data fetching

**2. Updated Files:**
- `custom_components/wunderground_scraper/coordinator.py` - Complete rewrite to use API
- `custom_components/wunderground_scraper/config_flow.py` - Added station ID extraction and validation
- `custom_components/wunderground_scraper/manifest.json` - Removed beautifulsoup4, bumped version to 0.2.0
- `debug/test_sensors.py` - Rewritten to use API instead of HTML parsing
- `debug/requirements.txt` - Removed beautifulsoup4
- `debug/README.md` - Updated documentation for API-based approach

**3. Improvements:**
- ✅ **100% sensor success rate** (vs ~50% with old scraper)
- ✅ All 12-15 sensor types now work reliably
- ✅ Support for both imperial and metric units in API
- ✅ Better error handling and logging
- ✅ Faster updates (direct API vs HTML parsing)
- ✅ More maintainable code

**4. API Data Mapping:**
```
API Field                → Home Assistant Sensor
─────────────────────────────────────────────────
imperial.temp            → temperature
imperial.heatIndex       → feels_like
imperial.dewpt           → dew_point
humidity                 → humidity
imperial.pressure        → pressure
imperial.windSpeed       → wind_speed
imperial.windGust        → wind_gust
winddir                  → wind_direction
imperial.precipRate      → precipitation_rate
imperial.precipTotal     → precipitation_accumulation
solarRadiation           → solar_radiation
uv                       → uv_index
```

**5. Backward Compatibility:**
- Still accepts Wunderground URLs in config
- Automatically extracts station ID from URL
- Can also accept just the station ID directly
- Existing configurations should work without changes

**6. Testing:**
```bash
# Test with the updated debug script
cd debug
python test_sensors.py KTXHOUST4430
# or
python test_sensors.py https://www.wunderground.com/dashboard/pws/KTXHOUST4430
```

### Fixed
- All sensors now report data correctly
- No more "not available" sensors due to HTML structure changes
- Temperature conversions (F to C) now more accurate
- Better handling of missing/null values

### Removed
- BeautifulSoup4 dependency
- All HTML parsing code
- User-agent randomization (no longer needed)

## [0.1.0] - Previous Version

### Initial Release
- HTML-based scraping of Wunderground PWS pages
- Support for 15 sensor types
- Celsius temperature conversion
