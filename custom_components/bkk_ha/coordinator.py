from __future__ import annotations

import logging
import async_timeout
from datetime import timedelta

from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .const import DOMAIN, CONF_STOPID, DEFAULT_SCAN_INTERVAL

_LOGGER = logging.getLogger(__name__)


class BKKDataUpdateCoordinator(DataUpdateCoordinator[dict]):
    """Class to manage fetching BKK data for a specific stop."""

    def __init__(self, hass: HomeAssistant, api_key: str, stop_config: dict) -> None:
        """Initialize the coordinator."""
        super().__init__(
            hass,
            _LOGGER,
            name=f"{DOMAIN}_{stop_config[CONF_STOPID]}",
            update_interval=timedelta(seconds=DEFAULT_SCAN_INTERVAL),
        )
        self.api_key = api_key
        self.stop_config = stop_config
        self.session = async_get_clientsession(hass)

    async def _async_update_data(self) -> dict:
        """Fetch data from BKK API."""
        stopid = self.stop_config[CONF_STOPID]
        minsafter = str(self.stop_config.get("mins_after", 60))
        minsbefore = str(self.stop_config.get("mins_before", 0))

        url = (
            f"https://go.bkk.hu/api/query/v1/ws/otp/api/where/arrivals-and-departures-for-stop.json"
            f"?key={self.api_key}&version=3&appVersion=apiary-1.0&onlyDepartures=true"
            f"&stopId={stopid}&minutesAfter={minsafter}&minutesBefore={minsbefore}"
        )

        try:
            async with async_timeout.timeout(30):
                response = await self.session.get(url)
                data = await response.json(content_type=None)

                if data.get("status") != "OK":
                    raise UpdateFailed(f"BKK API Error: {data.get('status')}")

                return data
        except Exception as err:
            raise UpdateFailed(f"Error communicating with BKK API: {err}") from err
