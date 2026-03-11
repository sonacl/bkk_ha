import voluptuous as vol
from homeassistant import config_entries
from homeassistant.core import callback
import homeassistant.helpers.config_validation as cv

from .const import (
    DOMAIN,
    CONF_APIKEY,
    CONF_STOPID,
    CONF_NAME,
    CONF_MAX_ITEMS,
    CONF_MINS_AFTER,
    CONF_MINS_BEFORE,
    CONF_WHEELCHAIR,
    CONF_BIKES,
    CONF_COLORS,
    CONF_IGNORE_NOW,
    CONF_IN_PREDICTED,
    CONF_STOPS,
)


class BKKStopConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for BKK Stop."""

    VERSION = 1

    async def async_step_user(self, user_input=None):
        """Initial setup: API Key."""
        if user_input is not None:
            # We save the API key and initialize an empty list of stops
            return self.async_create_entry(
                title="Budapest GO (BKK)",
                data={CONF_APIKEY: user_input[CONF_APIKEY]},
                options={CONF_STOPS: []},
            )

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_APIKEY): str,
                }
            ),
        )

    @staticmethod
    @callback
    def async_get_options_flow(config_entry):
        return BKKOptionsFlowHandler(config_entry)


class BKKOptionsFlowHandler(config_entries.OptionsFlow):
    """Handle options for BKK Stop."""

    def __init__(self, config_entry):
        self.config_entry = config_entry
        self.options = dict(config_entry.options)

    async def async_step_init(self, user_input=None):
        """Menu for adding or managing stops."""
        return self.async_show_menu(
            step_id="init", menu_options=["add_stop", "manage_stops"]
        )

    async def async_step_add_stop(self, user_input=None):
        """Step to add a new stop."""
        if user_input is not None:
            # Add new stop to the list
            if CONF_STOPS not in self.options:
                self.options[CONF_STOPS] = []

            self.options[CONF_STOPS].append(user_input)
            return self.async_create_entry(title="", data=self.options)

        return self.async_show_form(
            step_id="add_stop",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_STOPID): str,
                    vol.Optional(CONF_NAME): str,
                    vol.Optional(CONF_MAX_ITEMS, default=20): int,
                    vol.Optional(CONF_MINS_AFTER, default=60): int,
                    vol.Optional(CONF_MINS_BEFORE, default=0): int,
                    vol.Optional(CONF_IGNORE_NOW, default=True): bool,
                    vol.Optional(CONF_IN_PREDICTED, default=False): bool,
                    vol.Optional(CONF_WHEELCHAIR, default=False): bool,
                    vol.Optional(CONF_BIKES, default=False): bool,
                    vol.Optional(CONF_COLORS, default=True): bool,
                }
            ),
        )

    async def async_step_manage_stops(self, user_input=None):
        """Select a stop to remove (simple management)."""
        stops = self.options.get(CONF_STOPS, [])
        if not stops:
            return self.async_show_menu(step_id="no_stops", menu_options=["add_stop"])

        if user_input is not None:
            # Remove selected stop
            stop_to_remove = user_input["stop_to_remove"]
            self.options[CONF_STOPS] = [
                s for s in stops if s[CONF_STOPID] != stop_to_remove
            ]
            return self.async_create_entry(title="", data=self.options)

        stop_options = {
            s[CONF_STOPID]: f"{s.get(CONF_NAME, s[CONF_STOPID])} ({s[CONF_STOPID]})"
            for s in stops
        }

        return self.async_show_form(
            step_id="manage_stops",
            data_schema=vol.Schema(
                {
                    vol.Required("stop_to_remove"): vol.In(stop_options),
                }
            ),
        )
