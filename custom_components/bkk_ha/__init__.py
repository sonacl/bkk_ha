import logging
import os
from homeassistant.core import HomeAssistant
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform

from .const import DOMAIN, CONF_APIKEY, CONF_STOPS
from .coordinator import BKKDataUpdateCoordinator

_LOGGER = logging.getLogger(__name__)

PLATFORMS = [Platform.SENSOR]
URL_BASE = "/bkk_ha"


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up BKK Stop from a config entry."""
    hass.data.setdefault(DOMAIN, {})

    # Register the Lovelace card as a static path
    # This allows the card to be accessed at /bkk_stop/bkk-stop-card.js
    card_path = os.path.join(os.path.dirname(__file__), "bkk-stop-card.js")
    if os.path.exists(card_path):
        hass.http.register_static_path(f"{URL_BASE}/bkk-stop-card.js", card_path)

    api_key = entry.data[CONF_APIKEY]
    stops = entry.options.get(CONF_STOPS, [])

    coordinators = {}
    for stop_config in stops:
        stop_id = stop_config["stop_id"]
        coordinator = BKKDataUpdateCoordinator(hass, api_key, stop_config)
        await coordinator.async_config_entry_first_refresh()
        coordinators[stop_id] = coordinator

    hass.data[DOMAIN][entry.entry_id] = coordinators

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    entry.async_on_unload(entry.add_update_listener(update_listener))

    return True


async def update_listener(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Update listener for options."""
    await hass.config_entries.async_reload(entry.entry_id)


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id)

    return unload_ok
