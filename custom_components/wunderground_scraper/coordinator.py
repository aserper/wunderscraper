"""Data update coordinator for the Wunderground Scraper integration."""
import logging
from datetime import timedelta

import requests
from bs4 import BeautifulSoup

from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)


class WundergroundDataUpdateCoordinator(DataUpdateCoordinator):
    """Class to manage fetching data from the Wunderground website."""

    def __init__(self, hass, url):
        """Initialize."""
        self.url = url
        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=timedelta(minutes=5),
        )

    def _get_value_from_additional_conditions(self, soup, label):
        """Get a value from the 'Additional Conditions' section."""
        additional_conditions = soup.select_one("lib-additional-conditions")
        if additional_conditions:
            for row in additional_conditions.select(".row"):
                if label in row.text:
                    value_tag = row.select_one("span.wu-value.wu-value-to")
                    if value_tag:
                        return value_tag.text
        return None

    async def _async_update_data(self):
        """Update data via scraping."""
        try:
            response = await self.hass.async_add_executor_job(requests.get, self.url)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, "html.parser")

            data = {}
            data["temperature"] = soup.select_one("span.wu-value.wu-value-to").text
            data["dew_point"] = self._get_value_from_additional_conditions(
                soup, "Dew Point"
            )
            data["humidity"] = self._get_value_from_additional_conditions(
                soup, "Humidity"
            )
            data["pressure"] = self._get_value_from_additional_conditions(
                soup, "Pressure"
            )
            data[
                "precipitation_accumulation"
            ] = self._get_value_from_additional_conditions(soup, "Rainfall")

            wind_speed_tag = soup.select_one("header.wind-speed strong")
            if wind_speed_tag:
                data["wind_speed"] = wind_speed_tag.text

            wind_gust = self._get_value_from_additional_conditions(soup, "Wind Gust")
            if wind_gust:
                data["wind_gust"] = wind_gust

            precip_rate = self._get_value_from_additional_conditions(
                soup, "Precipitation Rate"
            )
            if precip_rate:
                data["precipitation_rate"] = precip_rate

            feels_like_tag = soup.select_one("div.feels-like span.temp")
            if feels_like_tag:
                data["feels_like"] = feels_like_tag.text.replace("°", "")

            return data
        except requests.exceptions.RequestException as e:
            raise UpdateFailed(f"Error communicating with Wunderground: {e}") from e
        except Exception as e:
            raise UpdateFailed(f"An unexpected error occurred: {e}") from e
