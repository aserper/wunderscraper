"""Data update coordinator for the Wunderground Scraper integration."""
import asyncio
import logging
import re
from datetime import timedelta

import requests

from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

# Public API key from Wunderground's website source
API_KEY = "e1f10a1e78da46f5b10a1e78da96f525"
API_ENDPOINT = "https://api.weather.com/v2/pws/observations/current"

# Weather.com's edge intermittently accepts no TCP connection at all (observed
# ~25% of requests), so a single failed poll is not evidence that the station is
# down. Retry a few times before believing a failure.
API_TIMEOUT = 10
MAX_ATTEMPTS = 3
RETRY_BACKOFF_SECONDS = 3

# If every retry fails for this many consecutive polls, stop serving the last
# reading and mark the entities unavailable. At the 5 minute update interval
# this is 30 minutes of continuous failure.
MAX_CONSECUTIVE_FAILURES = 6


class TransientFetchError(Exception):
    """Raised when a fetch fails in a way that is worth retrying."""


def extract_station_id(url):
    """Extract station ID from a Wunderground URL or bare station ID."""
    if not url:
        return None

    # Match pattern like: /pws/STATIONID (dashboard URL)
    match = re.search(r'/pws/([A-Z0-9]+)', url)
    if match:
        return match.group(1)

    # Match pattern like: /weather/us/ma/city/STATIONID (weather page URL)
    match = re.search(r'/weather/[^/]+/[^/]+/[^/]+/([A-Z0-9]+)', url)
    if match:
        return match.group(1)

    # Match any URL ending with a station ID pattern
    match = re.search(r'/([A-Z]{2,4}[A-Z0-9]+\d+)/?$', url)
    if match:
        return match.group(1)

    # If URL is just the station ID itself
    if re.match(r'^[A-Z0-9]+$', url):
        return url

    return None


def fahrenheit_to_celsius(fahrenheit):
    """Convert Fahrenheit to Celsius."""
    if fahrenheit is None:
        return None

    try:
        celsius = (float(fahrenheit) - 32) * 5 / 9
        return round(celsius, 1)
    except (ValueError, TypeError):
        _LOGGER.warning(f"Could not convert temperature '{fahrenheit}' to Celsius")
        return None


def parse_observations(api_data, station_id):
    """Map a Weather.com PWS API payload to Home Assistant sensor values."""
    observations = api_data.get('observations')
    if not observations:
        raise UpdateFailed(f"No observations data returned for station {station_id}")

    obs = observations[0]
    imperial = obs.get('imperial', {})

    # Map API data to Home Assistant sensor format
    data = {}

    # Temperature
    if imperial.get('temp') is not None:
        data['temperature'] = imperial['temp']
        data['temperature_celsius'] = fahrenheit_to_celsius(imperial['temp'])

    # Feels like (use heat index or wind chill, whichever is available)
    feels_like = imperial.get('heatIndex') or imperial.get('windChill')
    if feels_like is not None:
        data['feels_like'] = feels_like
        data['feels_like_celsius'] = fahrenheit_to_celsius(feels_like)

    # Dew point
    if imperial.get('dewpt') is not None:
        data['dew_point'] = imperial['dewpt']
        data['dew_point_celsius'] = fahrenheit_to_celsius(imperial['dewpt'])

    # Humidity
    if obs.get('humidity') is not None:
        data['humidity'] = obs['humidity']

    # Pressure
    if imperial.get('pressure') is not None:
        data['pressure'] = imperial['pressure']

    # Wind
    if imperial.get('windSpeed') is not None:
        data['wind_speed'] = imperial['windSpeed']

    if imperial.get('windGust') is not None:
        data['wind_gust'] = imperial['windGust']

    if obs.get('winddir') is not None:
        data['wind_direction'] = obs['winddir']

    # Precipitation
    if imperial.get('precipRate') is not None:
        data['precipitation_rate'] = imperial['precipRate']

    if imperial.get('precipTotal') is not None:
        data['precipitation_accumulation'] = imperial['precipTotal']

    # Solar radiation
    if obs.get('solarRadiation') is not None:
        data['solar_radiation'] = obs['solarRadiation']

    # UV index
    if obs.get('uv') is not None:
        data['uv_index'] = obs['uv']

    return data


def fetch_observations(station_id, timeout=API_TIMEOUT):
    """Fetch and parse the current observation for a station.

    Blocking; intended to run in an executor. Raises TransientFetchError for
    faults worth retrying (dropped connection, timeout, 5xx) and UpdateFailed
    for conditions retrying will not fix (204, unusable payload).
    """
    params = {
        'apiKey': API_KEY,
        'stationId': station_id,
        'format': 'json',
        'units': 'e',  # Imperial units
        'numericPrecision': 'decimal',
    }

    try:
        response = requests.get(API_ENDPOINT, params=params, timeout=timeout)
    except (requests.exceptions.ConnectionError, requests.exceptions.Timeout) as err:
        # ConnectionError covers ConnectTimeout, which is what a dropped TCP
        # connection to the edge produces.
        raise TransientFetchError(f"Could not reach Weather.com API: {err}") from err
    except requests.exceptions.RequestException as err:
        raise TransientFetchError(f"Error communicating with Weather.com API: {err}") from err

    if response.status_code == 204:
        raise UpdateFailed(f"Station {station_id} is not reporting data (HTTP 204)")

    if response.status_code >= 500:
        raise TransientFetchError(
            f"Weather.com API returned HTTP {response.status_code}"
        )

    try:
        response.raise_for_status()
        api_data = response.json()
    except (requests.exceptions.RequestException, ValueError) as err:
        raise UpdateFailed(f"Error parsing API response: {err}") from err

    return parse_observations(api_data, station_id)


async def fetch_with_retry(fetch, attempts=MAX_ATTEMPTS, backoff=RETRY_BACKOFF_SECONDS):
    """Run an async fetch callable, retrying only transient failures.

    Returns the fetch result. Raises the last error if every attempt fails, and
    propagates non-transient failures immediately without retrying.
    """
    last_error: TransientFetchError | None = None

    for attempt in range(1, attempts + 1):
        try:
            return await fetch()
        except TransientFetchError as err:
            last_error = err
            if attempt < attempts:
                _LOGGER.debug(
                    "Transient fetch failure (attempt %s/%s): %s; retrying in %ss",
                    attempt, attempts, err, backoff * attempt,
                )
                await asyncio.sleep(backoff * attempt)

    if last_error is None:
        raise TransientFetchError("Fetch failed without an error being recorded")
    raise last_error


class WundergroundDataUpdateCoordinator(DataUpdateCoordinator):
    """Class to manage fetching data from the Weather.com PWS API."""

    def __init__(self, hass, url):
        """Initialize."""
        # Extract station ID from URL
        self.station_id = extract_station_id(url)
        if not self.station_id:
            _LOGGER.error(
                "Could not extract station ID from URL: %s. "
                "Please use a valid Wunderground station URL like: "
                "https://www.wunderground.com/dashboard/pws/STATIONID or "
                "https://www.wunderground.com/weather/us/state/city/STATIONID",
                url
            )
            raise ValueError(
                f"Invalid Wunderground URL: {url}. "
                "Please reconfigure the integration with a valid station URL or station ID."
            )

        _LOGGER.info(f"Initialized coordinator for station: {self.station_id}")

        # Last successful reading, kept so a run of failed polls does not blank
        # every sensor in the dashboard and history.
        self._last_good_data = None
        self._consecutive_failures = 0

        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=timedelta(minutes=5),
        )

    @property
    def using_cached_data(self):
        """True when serving a held reading because the latest poll failed."""
        return self._consecutive_failures > 0

    async def _async_update_data(self):
        """Update data via Weather.com PWS API."""
        try:
            data = await fetch_with_retry(
                lambda: self.hass.async_add_executor_job(
                    fetch_observations, self.station_id
                )
            )
        except UpdateFailed:
            # Not transient: the station is silent or the payload is unusable.
            # Do not serve a stale reading for this.
            self._consecutive_failures = 0
            self._last_good_data = None
            raise
        except Exception as err:
            self._consecutive_failures += 1

            if (
                self._last_good_data is not None
                and self._consecutive_failures <= MAX_CONSECUTIVE_FAILURES
            ):
                _LOGGER.warning(
                    "Failed to fetch data for station %s (%s consecutive failures); "
                    "keeping last known reading",
                    self.station_id, self._consecutive_failures,
                )
                return self._last_good_data

            raise UpdateFailed(
                f"Failed to fetch data for station {self.station_id} "
                f"after {self._consecutive_failures} consecutive polls: {err}"
            ) from err

        self._consecutive_failures = 0
        self._last_good_data = data

        _LOGGER.debug(
            f"Successfully fetched data for {self.station_id}: {len(data)} sensors"
        )

        return data
