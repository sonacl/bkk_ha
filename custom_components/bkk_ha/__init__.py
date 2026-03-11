from __future__ import annotations

import logging
import os
import shutil
from homeassistant.core import HomeAssistant
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform

from .const import DOMAIN, CONF_APIKEY, CONF_STOPS
from .coordinator import BKKDataUpdateCoordinator

_LOGGER = logging.getLogger(__name__)

PLATFORMS = [Platform.SENSOR]


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up BKK Stop from a config entry."""

    # Copy the Lovelace card to HACS community folder for automatic serving
    await _setup_lovelace_card(hass)

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


async def _setup_lovelace_card(hass: HomeAssistant) -> None:
    """Set up the Lovelace card in the HACS community folder."""
    source_path = os.path.join(os.path.dirname(__file__), "bkk-stop-card.js")

    # Try HACS community folder first (for HACS users)
    community_path = hass.config.path("www/community/bkk_ha")
    www_path = hass.config.path("www")

    # Ensure www directory exists
    if not os.path.exists(www_path):
        os.makedirs(www_path)

    # If HACS community folder exists, use it
    if os.path.exists(hass.config.path("www/community")):
        if not os.path.exists(community_path):
            os.makedirs(community_path)
        dest_path = os.path.join(community_path, "bkk-stop-card.js")

        # Copy the card file
        if os.path.exists(source_path):
            await hass.async_add_executor_job(shutil.copy2, source_path, dest_path)
            _LOGGER.info("Copied bkk-stop-card.js to HACS community folder")
    else:
        # Fall back to regular www folder for non-HACS users
        dest_path = os.path.join(www_path, "bkk-stop-card.js")
        if os.path.exists(source_path):
            await hass.async_add_executor_job(shutil.copy2, source_path, dest_path)
            _LOGGER.info("Copied bkk-stop-card.js to www folder")


async def update_listener(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Update listener for options."""
    await hass.config_entries.async_reload(entry.entry_id)


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
