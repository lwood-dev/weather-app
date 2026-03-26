# Weather App

This app takes user input for a United States city and state, and a date range. It geocodes the location using the OpenStreetMap Nominatim API, retrieves 10 years of historical weather data from the Open-Meteo API, and displays the results in a table-per-year format via a desktop GUI. Weather data is cached in a local SQLite database to minimize redundant API calls on repeat queries.

## Libraries Used
- tkinter
- requests
- sqlite3
- datetime
- logging

## How to Run
Run `Weatherappfront.py` to launch the application.

## Version History
- **v1.0** — Initial completed application
- **v2.0** *(in progress)* — Refactor for PEP 8 compliance, improved readability, and better application of software engineering principles including DRY and Single Responsibility.