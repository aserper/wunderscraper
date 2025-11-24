"""Config flow for Wunderground Scraper."""
import re
import voluptuous as vol
from homeassistant import config_entries
from homeassistant.core import callback

from .const import DOMAIN


@config_entries.HANDLERS.register(DOMAIN)
class WundergroundScraperConfigFlow(config_entries.ConfigFlow):
    """Handle a config flow for Wunderground Scraper."""

    VERSION = 1

    def _validate_station_url(self, url):
        """Validate and extract station ID from URL."""
        # Match Wunderground PWS URL pattern
        match = re.search(r'/pws/([A-Z0-9]+)', url)
        if match:
            return match.group(1)
        
        # If it's just a station ID
        if re.match(r'^[A-Z0-9]+$', url):
            return url
        
        return None

    async def async_step_user(self, user_input=None):
        """Handle the initial step."""
        errors = {}
        if user_input is not None:
            # Validate the station URL/ID
            station_id = self._validate_station_url(user_input["url"])
            
            if not station_id:
                errors["url"] = "invalid_station_url"
            else:
                # Use station ID as unique identifier
                await self.async_set_unique_id(station_id)
                self._abort_if_unique_id_configured()
                
                # Create entry with a friendly title
                title = f"Wunderground {station_id}"
                return self.async_create_entry(title=title, data=user_input)

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema({vol.Required("url"): str}),
            errors=errors,
        )

    @staticmethod
    @callback
    def async_get_options_flow(config_entry):
        """Get the options flow for this handler."""
        return WundergroundScraperOptionsFlow(config_entry)


class WundergroundScraperOptionsFlow(config_entries.OptionsFlow):
    """Handle an options flow for Wunderground Scraper."""

    async def async_step_init(self, user_input=None):
        """Handle the initial step."""
        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)

        # Get current URL from options or data
        current_url = self.config_entry.options.get("url", self.config_entry.data.get("url", ""))

        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema(
                {
                    vol.Required("url", default=current_url): str
                }
            ),
        )
