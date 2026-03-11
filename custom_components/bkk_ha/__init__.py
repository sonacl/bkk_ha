from __future__ import annotations

import logging
from homeassistant.core import HomeAssistant
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform

from .const import DOMAIN, CONF_APIKEY, CONF_STOPS
from .coordinator import BKKDataUpdateCoordinator

_LOGGER = logging.getLogger(__name__)

PLATFORMS = [Platform.SENSOR]


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up BKK Stop from a config entry."""

    # Note: The Lovelace card should be manually added to www folder
    # or served through a different mechanism if needed

    api_key = entry.data[CONF_APIKEY]
    stops = entry.options.get(CONF_STOPS, [])

    coordinators: dict[str, BKKDataUpdateCoordinator] = {}
    for stop_config in stops:
        stop_id = stop_config["stop_id"]
        coordinator = BKKDataUpdateCoordinator(hass, api_key, stop_config)
        await coordinator.async_config_entry_first_refresh()
        coordinators[stop_id] = coordinator

    # Store data directly in the entry
    entry.runtime_data = coordinators

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    entry.async_on_unload(entry.add_update_listener(update_listener))

    return True


async def update_listener(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Update listener for options."""
    await hass.config_entries.async_reload(entry.entry_id)


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
