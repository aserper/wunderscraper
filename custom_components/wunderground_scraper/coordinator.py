"""Data update coordinator for the Wunderground Scraper integration."""
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


class WundergroundDataUpdateCoordinator(DataUpdateCoordinator):
    """Class to manage fetching data from the Weather.com PWS API."""

    def __init__(self, hass, url):
        """Initialize."""
        # Extract station ID from URL
        self.station_id = self._extract_station_id(url)
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
        
        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=timedelta(minutes=5),
        )

    def _extract_station_id(self, url):
        """Extract station ID from Wunderground URL."""
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

    def _fahrenheit_to_celsius(self, fahrenheit):
        """Convert Fahrenheit to Celsius."""
        if fahrenheit is None:
            return None
        
        try:
            celsius = (float(fahrenheit) - 32) * 5 / 9
            return round(celsius, 1)
        except (ValueError, TypeError):
            _LOGGER.warning(f"Could not convert temperature '{fahrenheit}' to Celsius")
            return None

    async def _async_update_data(self):
        """Update data via Weather.com PWS API."""
        try:
            # Build API URL
            params = {
                'apiKey': API_KEY,
                'stationId': self.station_id,
                'format': 'json',
                'units': 'e',  # Imperial units
                'numericPrecision': 'decimal'
            }
            
            # Make API request
            response = await self.hass.async_add_executor_job(
                lambda: requests.get(API_ENDPOINT, params=params, timeout=10)
            )
            
            if response.status_code == 204:
                raise UpdateFailed(f"Station {self.station_id} is not reporting data (HTTP 204)")
            
            response.raise_for_status()
            api_data = response.json()
            
            # Extract observation data
            if not api_data.get('observations') or len(api_data['observations']) == 0:
                raise UpdateFailed(f"No observations data returned for station {self.station_id}")
            
            obs = api_data['observations'][0]
            imperial = obs.get('imperial', {})
            
            # Map API data to Home Assistant sensor format
            data = {}
            
            # Temperature
            if imperial.get('temp') is not None:
                data['temperature'] = imperial['temp']
                data['temperature_celsius'] = self._fahrenheit_to_celsius(imperial['temp'])
            
            # Feels like (use heat index or wind chill, whichever is available)
            feels_like = imperial.get('heatIndex') or imperial.get('windChill')
            if feels_like is not None:
                data['feels_like'] = feels_like
                data['feels_like_celsius'] = self._fahrenheit_to_celsius(feels_like)
            
            # Dew point
            if imperial.get('dewpt') is not None:
                data['dew_point'] = imperial['dewpt']
                data['dew_point_celsius'] = self._fahrenheit_to_celsius(imperial['dewpt'])
            
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
            
            _LOGGER.debug(f"Successfully fetched data for {self.station_id}: {len(data)} sensors")
            
            return data
            
        except requests.exceptions.Timeout:
            raise UpdateFailed(f"Timeout while fetching data for station {self.station_id}")
        except requests.exceptions.RequestException as e:
            raise UpdateFailed(f"Error communicating with Weather.com API: {e}") from e
        except (KeyError, ValueError) as e:
            raise UpdateFailed(f"Error parsing API response: {e}") from e
        except Exception as e:
            raise UpdateFailed(f"Unexpected error occurred: {e}") from e
