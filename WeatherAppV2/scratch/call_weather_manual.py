import weatherappbackV2

date_list = [("2026-01-01", "2026-01-05")]
lat, lon = weatherappbackV2.call_coordinates_api("Morristown", "NJ")
weather_data = weatherappbackV2.call_weather_api(lat, lon, date_list)
print(weather_data)