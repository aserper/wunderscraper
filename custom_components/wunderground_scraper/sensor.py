"""Platform for sensor integration."""
from __future__ import annotations

from homeassistant.components.sensor import SensorDeviceClass, SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import WundergroundDataUpdateCoordinator

SENSOR_TYPES = {
    "temperature": {
        "name": "Temperature",
        "unit": "°F",
        "device_class": SensorDeviceClass.TEMPERATURE,
    },
    "dew_point": {
        "name": "Dew Point",
        "unit": "°F",
        "device_class": SensorDeviceClass.TEMPERATURE,
    },
    "humidity": {
        "name": "Humidity",
        "unit": "%",
        "device_class": SensorDeviceClass.HUMIDITY,
    },
    "wind_speed": {
        "name": "Wind Speed",
        "unit": "mph",
        "device_class": SensorDeviceClass.WIND_SPEED,
    },
    "wind_gust": {
        "name": "Wind Gust",
        "unit": "mph",
        "device_class": SensorDeviceClass.WIND_SPEED,
    },
    "pressure": {
        "name": "Pressure",
        "unit": "in",
        "device_class": SensorDeviceClass.PRESSURE,
    },
    "precipitation_rate": {
        "name": "Precipitation Rate",
        "unit": "in/hr",
        "device_class": SensorDeviceClass.PRECIPITATION_INTENSITY,
    },
    "precipitation_accumulation": {
        "name": "Precipitation Accumulation",
        "unit": "in",
        "device_class": SensorDeviceClass.PRECIPITATION,
    },
}


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the sensor platform."""
    coordinator: WundergroundDataUpdateCoordinator = hass.data[DOMAIN][
        config_entry.entry_id
    ]

    sensors = []
    for sensor_type in SENSOR_TYPES:
        if coordinator.data and sensor_type in coordinator.data:
            sensors.append(WundergroundSensor(coordinator, config_entry, sensor_type))
    async_add_entities(sensors)


class WundergroundSensor(CoordinatorEntity, SensorEntity):
    """Representation of a Sensor."""

    def __init__(
        self,
        coordinator: WundergroundDataUpdateCoordinator,
        config_entry: ConfigEntry,
        sensor_type: str,
    ):
        """Initialize the sensor."""
        super().__init__(coordinator)
        self._sensor_type = sensor_type
        sensor_info = SENSOR_TYPES[sensor_type]

        self._attr_name = f"{config_entry.title} {sensor_info['name']}"
        self._attr_native_unit_of_measurement = sensor_info["unit"]
        self._attr_device_class = sensor_info.get("device_class")
        self._attr_unique_id = f"{config_entry.unique_id}_{self._sensor_type}"

    @property
    def native_value(self):
        """Return the state of the sensor."""
        if self.coordinator.data:
            return self.coordinator.data.get(self._sensor_type)
        return None

    @property
    def available(self) -> bool:
        """Return if entity is available."""
        return (
            self.coordinator.last_update_success
            and self.coordinator.data is not None
            and self._sensor_type in self.coordinator.data
        )
