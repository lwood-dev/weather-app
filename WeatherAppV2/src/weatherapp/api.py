import weatherappbackV2
import database


def safe_api(url, params, header):
    """
    Sends a GET request to an API and safely handles network/parsing errors.

    Wraps requests.get() in a try/except so that any network or JSON-decoding
    failure is caught and reported as a value instead of raising and crashing
    the program. This lets callers check for an error rather than wrapping every
    call in their own try/except.

    Args:
        url (str): The endpoint to send the GET request to.
        params (dict): Query-string parameters for the request.
        header (dict or None): Request headers (e.g. a User-Agent). May be None.

    Returns:
        tuple: (data, error), where exactly one is None.
            On success: (parsed_json, None)
            On failure: (None, error_message_string)
    """
    try:
        # timeout=10 prevents the request from hanging indefinitely if the
        # server never responds.
        response = requests.get(url, params=params, headers=header, timeout=10)
        data = response.json()
        return data, None
    except requests.exceptions.Timeout:
        return None, "Timeout"
    except requests.exceptions.ConnectionError:
        return None, "Connection Error"
    except requests.exceptions.HTTPError:
        return None, "HTTP"
    except requests.exceptions.JSONDecodeError:
        return None, "Not JSON Code"
    # RequestException is the base class for all requests errors, so this is a
    # catch-all that must come LAST — otherwise it would swallow the more
    # specific exceptions above before they could be matched.
    except requests.exceptions.RequestException:
        return None, "There was an error with the request"


def extract_lat_lon(response):
    """
    Pulls latitude and longitude out of a Nominatim geocoding response.

    The Nominatim API returns a list of matching locations; this takes the
    first (best) match at index 0. The API delivers lat/lon as strings, so
    they are converted to floats before rounding.

    Args:
        response (list): Parsed JSON from the Nominatim API — a list of dicts,
                         each with "lat" and "lon" string keys.

    Returns:
        tuple: (Lat, Lon) as floats rounded to 2 decimal places.
    """
    # float() is required because the API returns these as strings; round()
    # cannot operate on a string.
    Lat = round(float(response[0]["lat"]), 2)
    Lon = round(float(response[0]["lon"]), 2)
    return Lat, Lon


def build_wd(api_response):
    """
    Transforms raw Open-Meteo API responses into the standardized weather
    data structure, grouped by year.

    Takes the list of per-year API responses and, for each one, walks the
    parallel "daily" arrays (dates, weather codes, high/low temps) in lockstep,
    packaging each day into a single tuple.

    Args:
        api_response (list): A list of parsed Open-Meteo responses, one per
                             year. Each response is a dict containing a "daily"
                             key whose value holds parallel lists: "time",
                             "weather_code", "temperature_2m_max", and
                             "temperature_2m_min".

    Returns:
        dict: Keys are 4-digit year strings (e.g. "2024"). Values are lists of
              (date, temp_high, temp_low, weather_code) tuples for that year.
              Note this tuple order matches the database's (date, temp_high,
              temp_low, weather) shape used by build_db_data().
    """
    weather_data = {}
    for year in api_response:
        yr_weather = []
        weather = year["daily"]
        # Derive the year label from the first date in this response
        # (e.g. "2024-06-15" -> "2024").
        year_str = weather["time"][0][0:4]
        # zip() walks the four parallel arrays together, yielding one day at a
        # time. This relies on all four lists being the same length and in the
        # same date order, which the API guarantees.
        for time, weather_code, temperature_2m_max, temperature_2m_min in zip(
            weather["time"],
            weather["weather_code"],
            weather["temperature_2m_max"],
            weather["temperature_2m_min"],
        ):
            date = time
            wc = weather_code
            t_max = temperature_2m_max
            t_min = temperature_2m_min
            yr_weather.append((date, t_max, t_min, wc))
        weather_data[year_str] = yr_weather
    return weather_data


def _call_weather_api_raw(Lat, Lon, date_list):
    api_response = []
    url = "https://historical-forecast-api.open-meteo.com/v1/forecast"
    for start_date, end_date in date_list:
        params = {
            "latitude": Lat,
            "longitude": Lon,
            "start_date": start_date,
            "end_date" : end_date,
            "daily": ["weather_code", "temperature_2m_max", "temperature_2m_min"]
        }
        response, error = safe_api(url, params, header=None)
        if error:
            messagebox.showerror("Error", error)
            return None, error
        api_response.append(response)
    weather_data = build_wd(api_response)
    return weather_data


def call_weather_api(Lat, Lon, date_list):
    """
    Fetches historical weather data from Open-Meteo for a location across
    multiple date ranges (one per year).

    Loops over each (start_date, end_date) range, requests that year's daily
    weather, and collects the raw responses. Once all ranges are fetched, hands
    them to build_wd() to produce the standardized data structure.

    Args:
        Lat (float): Latitude of the location.
        Lon (float): Longitude of the location.
        date_list (list): List of (start_date, end_date) tuples, one per year,
                          with dates as "YYYY-MM-DD" strings.

    Returns:
        tuple: (weather_data, error), where exactly one is None.
            On success: (weather_data_dict, None). See build_wd() for the dict
                        shape.
            On failure: (None, error_message_string).

    Note:
        The success branch currently returns a bare `weather_data` rather than
        `(weather_data, None)`. To honor the (data, error) contract described
        above, the final line should be `return weather_data, None`.
    """
    api_response = []
    url = "https://historical-forecast-api.open-meteo.com/v1/forecast"
    # One API request per year: each date_list entry is that year's range.
    for start_date, end_date in date_list:
        params = {
            "latitude": Lat,
            "longitude": Lon,
            "start_date": start_date,
            "end_date" : end_date,
            "daily": ["weather_code", "temperature_2m_max", "temperature_2m_min"]
        }
        response, error = safe_api(url, params, header=None)
        if error:
            # Surface the error to the user via a GUI popup, then bail out of
            # the whole batch — a partial result would be misleading.
            messagebox.showerror("Error", error)
            return None, error
        api_response.append(response)
    weather_data = build_wd(api_response)
    return weather_data


def _call_coordinates_api_raw(city, state):
    url = "https://nominatim.openstreetmap.org/search"
    params = {
        "city" : city, 
        "state" : state,
        "format": "json"
        }
    header = {
        "User-Agent": "WeatherApp/1.0"
    }
    response, error = safe_api(url, params, header)
    if error:
        messagebox.showerror("Error", error)
        return None, error
    Lat, Lon = extract_lat_lon(response)
    return Lat, Lon


def call_coordinates_api(city, state):
    """
    Geocodes a city/state into latitude and longitude using the Nominatim API.

    Args:
        city (str): City name to look up.
        state (str): State name to disambiguate the city.

    Returns:
        tuple: (Lat, Lon) as floats on success, or (None, error_message_string)
               on failure.

    Note:
        Nominatim's usage policy requires a descriptive User-Agent header, which
        is why one is supplied here (unlike the Open-Meteo call).
    """
    url = "https://nominatim.openstreetmap.org/search"
    params = {
        "city" : city, 
        "state" : state,
        "format": "json"  # ask Nominatim to return JSON rather than HTML/XML
        }
    # Nominatim's terms of use require identifying your application via a
    # User-Agent header; requests without one may be rejected.
    header = {
        "User-Agent": "WeatherApp/1.0"
    }
    response, error = safe_api(url, params, header)
    if error:
        messagebox.showerror("Error", error)
        return None, error
    Lat, Lon = extract_lat_lon(response)
    return Lat, Lon