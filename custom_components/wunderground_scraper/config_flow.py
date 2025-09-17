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
        errors = {}
        if user_input is not None:
            # Here you would validate the user input, for example,
            # check if the URL is a valid Wunderground URL.
            # For now, we'll just accept any URL.
            await self.async_set_unique_id(user_input["url"])
            self._abort_if_unique_id_configured()
            return self.async_create_entry(title="Wunderground Scraper", data=user_input)

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
