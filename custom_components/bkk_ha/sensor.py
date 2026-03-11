from __future__ import annotations

import logging
import zoneinfo
from datetime import datetime

from homeassistant.components.sensor import (
    SensorEntity,
    ENTITY_ID_FORMAT,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.helpers.entity import async_generate_entity_id

from .const import (
    DOMAIN,
    CONF_STOPID,
    CONF_IGNORE_NOW,
    CONF_IN_PREDICTED,
    CONF_MAX_ITEMS,
    CONF_COLORS,
    CONF_WHEELCHAIR,
    CONF_BIKES,
    CONF_ATTRIBUTION,
    CONF_STOPS,
    CONF_NAME,
)
from .coordinator import BKKDataUpdateCoordinator

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the BKK sensors from a config entry."""
    # Use runtime_data instead of hass.data
    coordinators: dict[str, BKKDataUpdateCoordinator] = entry.runtime_data
    stops = entry.options.get(CONF_STOPS, [])

    entities = []
    for stop_config in stops:
        stop_id = stop_config[CONF_STOPID]
        if stop_id in coordinators:
            entities.append(BKKStopSensor(coordinators[stop_id], stop_config, entry))

    async_add_entities(entities)


class BKKStopSensor(CoordinatorEntity[BKKDataUpdateCoordinator], SensorEntity):
    """Sensor that displays BKK departures for a specific stop."""

    _attr_has_entity_name = True
    _attr_attribution = CONF_ATTRIBUTION

    def __init__(
        self,
        coordinator: BKKDataUpdateCoordinator,
        stop_config: dict,
        entry: ConfigEntry,
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator)
        self._stop_config = stop_config
        self._entry = entry
        self._stopid = stop_config[CONF_STOPID]
        self._attr_unique_id = f"bkk_ha_{self._stopid}"
        self._attr_name = stop_config.get(CONF_NAME) or f"BKK Stop {self._stopid}"
        # self.hass is not available in __init__, so timezone is fetched lazily via property

        self.entity_id = async_generate_entity_id(
            ENTITY_ID_FORMAT, f"bkk_ha_{self._stopid}", hass=coordinator.hass
        )

    @property
    def _tz(self) -> zoneinfo.ZoneInfo:
        """Return timezone lazily — self.hass is only available after __init__."""
        return zoneinfo.ZoneInfo(self.hass.config.time_zone)

    @property
    def native_value(self) -> str:
        """Return next departure in minutes."""
        vehicles = self.extra_state_attributes.get("vehicles", [])
        return vehicles[0]["in"] if vehicles else "No service"

    @property
    def extra_state_attributes(self) -> dict:
        """Return the extra state attributes used by the Lovelace card."""
        data = self.coordinator.data
        if not data or "data" not in data:
            return {}

        try:
            res = {
                "stationName": data["data"]["references"]["stops"][self._stopid][
                    "name"
                ],
                "vehicles": [],
                "updatedAt": datetime.now().strftime("%Y/%m/%d %H:%M"),
            }

            current_time = int(data["currentTime"] / 1000)
            stoptimes = data.get("data", {}).get("entry", {}).get("stopTimes", [])

            for stop in stoptimes:
                target_time = (
                    stop.get("predictedDepartureTime")
                    if (
                        self._stop_config.get(CONF_IN_PREDICTED)
                        and stop.get("predictedDepartureTime")
                    )
                    else stop.get("departureTime", 0)
                )
                diff = int((target_time - current_time) / 60)

                if diff < 0:
                    diff = 0
                if self._stop_config.get(CONF_IGNORE_NOW) and diff == 0:
                    continue

                trip_id = stop.get("tripId")
                route_id = data["data"]["references"]["trips"][trip_id]["routeId"]
                route = data["data"]["references"]["routes"][route_id]

                v_info = {
                    "in": str(diff),
                    "type": route.get("type", "BUS"),
                    "routeid": route.get("iconDisplayText", "?"),
                    "headsign": stop.get("stopHeadsign", "?"),
                    "attime": datetime.fromtimestamp(
                        stop.get("departureTime"), self._tz
                    ).strftime("%H:%M"),
                }

                if stop.get("predictedDepartureTime"):
                    v_info["predicted_attime"] = datetime.fromtimestamp(
                        stop.get("predictedDepartureTime"), self._tz
                    ).strftime("%H:%M")

                if self._stop_config.get(CONF_COLORS):
                    v_info["color"] = route.get("color")
                    v_info["textcolor"] = route.get("textColor")

                if self._stop_config.get(CONF_WHEELCHAIR):
                    v_info["wheelchair"] = str(
                        data["data"]["references"]["trips"][trip_id].get(
                            "wheelchairAccessible", "0"
                        )
                    )

                if self._stop_config.get(CONF_BIKES):
                    v_info["bikesallowed"] = data["data"]["references"]["trips"][
                        trip_id
                    ].get("bikesAllowed", "0")

                res["vehicles"].append(v_info)

                max_items = self._stop_config.get(CONF_MAX_ITEMS, 20)
                if max_items > 0 and len(res["vehicles"]) >= max_items:
                    break

            return res
        except Exception:
            _LOGGER.exception("Error parsing BKK data for stop: %s", self._stopid)
            return {}

    @property
    def icon(self) -> str:
        return "mdi:bus"
