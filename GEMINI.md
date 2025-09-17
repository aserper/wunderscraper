### Project Overview

This project is a custom integration for Home Assistant designed to scrape weather data from a user-specified Wunderground Personal Weather Station (PWS) URL. It extracts key weather metrics from the page's HTML and presents them as sensor entities within Home Assistant.

The integration is built using Python and follows modern Home Assistant development standards. It leverages the `DataUpdateCoordinator` pattern to efficiently manage data fetching in the background.

**Key Technologies:**
- **Python 3**
- **Home Assistant Core**
- **BeautifulSoup4:** For parsing the HTML content from the Wunderground page.
- **Requests:** For making HTTP requests to fetch the page data.

**Architecture:**
- `__init__.py`: Initializes the integration, sets up the data update coordinator, and forwards the configuration to the sensor platform.
- `coordinator.py`: Contains the `WundergroundDataUpdateCoordinator` class, which is responsible for periodically fetching and parsing the weather data from the specified URL.
- `sensor.py`: Defines the `WundergroundSensor` entities. It maps the data scraped by the coordinator to individual Home Assistant sensors with appropriate device classes (e.g., temperature, humidity).
- `config_flow.py`: Manages the user configuration flow through the Home Assistant UI, allowing the user to input the Wunderground station URL.
- `manifest.json`: Provides metadata for the integration, including the domain, name, version, and Python package requirements.

### Building and Running

This is a Home Assistant integration and is not intended to be run as a standalone application.

**Installation & Execution:**
1.  Copy the `custom_components/wunderground_scraper` directory into the `<config>/custom_components/` directory of your Home Assistant instance.
2.  Restart Home Assistant.
3.  Navigate to **Settings > Devices & Services**, click **Add Integration**, and search for "Wunderground Scraper" to configure it with a PWS URL.

**Testing:**

```
# TODO: Add instructions for running tests once a test suite is created.
```

### Development Conventions

- **Coordinator Pattern:** All data fetching is centralized in the `WundergroundDataUpdateCoordinator` to avoid blocking I/O and to allow multiple entities to share the same data source.
- **Asynchronous Operations:** The codebase uses `async` and `await` for all I/O-bound operations to comply with Home Assistant's asynchronous architecture.
- **Entity Definition:** Sensors are defined in the `SENSOR_TYPES` dictionary in `sensor.py`. To add a new sensor, a new entry must be added to this dictionary and the corresponding scraping logic must be added to `coordinator.py`.
- **Configuration:** User setup is handled exclusively through the UI via the `ConfigFlow` handlers.
