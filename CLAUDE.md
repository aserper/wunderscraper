# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a Home Assistant custom integration that scrapes weather data from Wunderground Personal Weather Station (PWS) pages without requiring an API key. It extracts weather metrics from HTML and presents them as sensor entities in Home Assistant.

## Architecture

The integration follows the Home Assistant DataUpdateCoordinator pattern:

- **coordinator.py**: Central data fetching logic using BeautifulSoup4 to scrape Wunderground HTML pages. Updates every 5 minutes.
- **sensor.py**: Defines sensor entities that map scraped data to Home Assistant sensors with appropriate device classes
- **config_flow.py**: UI-based configuration flow for entering the PWS URL
- **__init__.py**: Entry point that initializes the coordinator and forwards to sensor platform

Data flow: Wunderground HTML → Coordinator (scrapes) → Sensor entities → Home Assistant

## Development Workflow

### Testing Changes
Since this is a Home Assistant integration, test by:
1. Copy `custom_components/wunderground_scraper/` to your Home Assistant `custom_components/` directory
2. Restart Home Assistant
3. Configure via Settings > Devices & Services > Add Integration > "Wunderground Scraper"

### Adding New Sensors
1. Add scraping logic in `coordinator.py` `_async_update_data()` method
2. Add sensor definition to `SENSOR_TYPES` dictionary in `sensor.py`
3. Ensure proper device class and unit of measurement

## Key Conventions

- All I/O operations must be async (use `hass.async_add_executor_job` for sync libraries)
- Follow Home Assistant's entity naming conventions
- Data fetching centralized in coordinator to avoid blocking I/O
- HTML parsing uses specific CSS selectors that may break if Wunderground changes their layout