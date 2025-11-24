"""Config flow for Wunderground Scraper."""
import voluptuous as vol
from homeassistant import config_entries
from homeassistant.core import callback

from .const import DOMAIN


@config_entries.HANDLERS.register(DOMAIN)
class WundergroundScraperConfigFlow(config_entries.ConfigFlow):
    """Handle a config flow for Wunderground Scraper."""

    VERSION = 1

    async def async_step_user(self, user_input=None):
        """Handle the initial step."""
        if user_input is not None:
            # Accept any non-empty URL/station ID
            url = user_input.get("url", "").strip()
            if url:
                return self.async_create_entry(title="Wunderground Scraper", data=user_input)
            else:
                # Show error if empty
                return self.async_show_form(
                    step_id="user",
                    data_schema=vol.Schema({vol.Required("url"): str}),
                    errors={"url": "required"},
                )

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema({vol.Required("url"): str}),
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

        # Get current URL from data
        current_url = self.config_entry.data.get("url", "")

        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema(
                {
                    vol.Required("url", default=current_url): str
                }
            ),
        )
