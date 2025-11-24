"""Platform for sensor integration."""
from __future__ import annotations
import logging

from homeassistant.components.sensor import SensorDeviceClass, SensorEntity, SensorStateClass
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import WundergroundDataUpdateCoordinator

_LOGGER = logging.getLogger(__name__)

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
        "unit": "inHg",
        "device_class": SensorDeviceClass.PRESSURE,
    },
    "precipitation_rate": {
        "name": "Precipitation Rate",
        "unit": "in/h",
        "device_class": SensorDeviceClass.PRECIPITATION_INTENSITY,
    },
    "precipitation_accumulation": {
        "name": "Precipitation Accumulation",
        "unit": "in",
        "device_class": SensorDeviceClass.PRECIPITATION,
    },
    "feels_like": {
        "name": "Feels Like",
        "unit": "°F",
        "device_class": SensorDeviceClass.TEMPERATURE,
    },
    "temperature_celsius": {
        "name": "Temperature (Celsius)",
        "unit": "°C",
        "device_class": None,  # Bypass HA's automatic unit conversion
        "state_class": SensorStateClass.MEASUREMENT,
        "temperature_sensor": True,  # Custom attribute to identify as temperature
    },
    "feels_like_celsius": {
        "name": "Feels Like (Celsius)",
        "unit": "°C",
        "device_class": None,  # Bypass HA's automatic unit conversion
        "state_class": SensorStateClass.MEASUREMENT,
        "temperature_sensor": True,  # Custom attribute to identify as temperature
    },
    "dew_point_celsius": {
        "name": "Dew Point (Celsius)",
        "unit": "°C",
        "device_class": None,  # Bypass HA's automatic unit conversion
        "state_class": SensorStateClass.MEASUREMENT,
        "temperature_sensor": True,  # Custom attribute to identify as temperature
    },
    "visibility": {
        "name": "Visibility",
        "unit": "mi",
        "device_class": SensorDeviceClass.DISTANCE,
        "state_class": SensorStateClass.MEASUREMENT,
    },
    "clouds": {
        "name": "Sky Condition",
        "unit": None,
        "device_class": None,
    },
    "snow_depth": {
        "name": "Snow Depth",
        "unit": "in",
        "device_class": SensorDeviceClass.DISTANCE,
        "state_class": SensorStateClass.MEASUREMENT,
    },
    "wind_direction": {
        "name": "Wind Direction",
        "unit": "°",
        "device_class": None,
    },
    "uv_index": {
        "name": "UV Index",
        "unit": None,
        "device_class": None,
        "state_class": SensorStateClass.MEASUREMENT,
    },
    "solar_radiation": {
        "name": "Solar Radiation",
        "unit": "W/m²",
        "device_class": SensorDeviceClass.IRRADIANCE,
        "state_class": SensorStateClass.MEASUREMENT,
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

    # Define temperature sensor mappings for Celsius creation
    celsius_mappings = {
        "temperature_celsius": "temperature",
        "feels_like_celsius": "feels_like",
        "dew_point_celsius": "dew_point"
    }

    for sensor_type in SENSOR_TYPES:
        should_create = False

        if sensor_type in celsius_mappings:
            # For Celsius sensors, create if the corresponding Fahrenheit sensor exists
            fahrenheit_sensor = celsius_mappings[sensor_type]
            should_create = coordinator.data and fahrenheit_sensor in coordinator.data
        else:
            # For all other sensors, create if data exists
            should_create = coordinator.data and sensor_type in coordinator.data

        if should_create:
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
        self._attr_state_class = sensor_info.get("state_class")
        self._attr_unique_id = f"{config_entry.unique_id}_{self._sensor_type}"

        # Add custom attributes for Celsius sensors
        if sensor_info.get("temperature_sensor"):
            self._attr_extra_state_attributes = {
                "temperature_sensor": True,
                "original_unit": "fahrenheit",
                "conversion_applied": True
            }


    @property
    def native_value(self):
        """Return the state of the sensor."""
        if self.coordinator.data:
            return self.coordinator.data.get(self._sensor_type)
        return None

    @property
    def available(self) -> bool:
        """Return if entity is available."""
        if not (self.coordinator.last_update_success and self.coordinator.data is not None):
            return False

        # For Celsius sensors, check if corresponding Fahrenheit sensor exists
        celsius_mappings = {
            "temperature_celsius": "temperature",
            "feels_like_celsius": "feels_like",
            "dew_point_celsius": "dew_point"
        }

        if self._sensor_type in celsius_mappings:
            fahrenheit_sensor = celsius_mappings[self._sensor_type]
            return fahrenheit_sensor in self.coordinator.data
        else:
            return self._sensor_type in self.coordinator.data
