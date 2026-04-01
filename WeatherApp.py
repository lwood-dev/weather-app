import requests
import json
from datetime import datetime
from tkinter import ttk
import logging
import sqlite3


##API Callers

def safe_api_call(url, params=None, headers=None, timeout=10):
    """
    Makes a GET request to the specified URL and handles common API errors.

    Args:
        url: The API endpoint URL as a string
        params: Optional dictionary of query parameters
        headers: Optional dictionary of request headers
        timeout: Request timeout in seconds (default 10)

    Returns:
        Tuple of (data, error). On success: (dict, None).
        On failure: (None, error_string).
    """
    
    try:
        response = requests.get(url, params=params, headers=headers, timeout=timeout)
        response.raise_for_status()
        data = response.json()
        return data, None
    except requests.exceptions.Timeout:
        return None, "timeout"
    except requests.exceptions.ConnectionError:
        return None, "connection_error"
    except requests.exceptions.HTTPError:
        return None, "http_error"
    except requests.exceptions.JSONDecodeError:
        return None, "invalid_json"
    except requests.exceptions.RequestException:
        return None, "request_failed"

def geo_convert(location_state,location_city):
    """
    Converts user-input state and city into latitude/longitude coordinates using the OpenStreetMap Nominatim API via safe_api_call(). 
    Receives the results of safe_api_call as variable "data", a single item list composed of a dictionary with latitude and longitude
    found at keys "lat" and "lon".
    
    Args:
        location_city: user-input as string via textbox of a United States city
        location_state: user-input as string from preset list of the 50 US states.
        
    Returns:
        Tuple of latitude, longitude, and error=none
        On Failure: None, none, error type. 

    Thoughts for V2: 
        Should this be broken up into more functions? "Too many concerns".
        Is the error handling redundant given safe_api_call() has error handling and the if statement checks for returned information?
            Is it even possible for us to have a keyerror or indexerror given the safeguards already in place?
    """
    logging.info(f"Converting location: {location_city}, {location_state}")
    
    url = "https://nominatim.openstreetmap.org/search"
    params = {
        "city" : location_city,
        "state" : location_state,
        "country" : "USA",
        "format" : "json"
    }
    headers = {
        "User-Agent": "WeatherApp/1.0"
    }
    data, error = safe_api_call(url, params, headers, timeout=10)    
    if error:
        logging.error(f"Geocoding failed for {location_city}, {location_state}: {error}")
        return None, None, error
    if len(data) == 0: # For a valid API response but location not found (returned an empty list)
        logging.warning(f"Location not found: {location_city}, {location_state}")
        return None, None, "location_not_found"
    try:
        latitude = data[0]["lat"]
        longitude = data[0]["lon"]
        logging.info(f"Successfully geocoded to lat={latitude}, lon={longitude}")
    except (KeyError, IndexError):
        logging.error(f"Invalid geocoding response format for {location_city}, {location_state}")
        return None, None, "invalid_response_format"
    return latitude, longitude, None

def get_weather(latitude, longitude, dates):
    """
    Makes an API call to Open-Meteo with latitude and longitude coordinates and a list of dates
    covering the user-input date range. 
    API call returns weather data as a JSON, which the requests library converts to a Python dictionary via response.json().  
    Data structure:
        [
            {   #One dictionary per year
                "latitude": float,
                "longitude": float,
                "daily": {
                    "time": [list of date strings],
                    "temperature_2m_max": [list of floats],
                    "temperature_2m_min": [list of floats],
                    "weather_code": [list of ints],
                    }
                }
            ] 
        
    ARGS:
        latitude: Latitude coordinates created by geo_convert()
        longitude: Longitude coordinates created by geo_convert()
        dates: list of dates in format string YYYY-MM-DD to call the API with.

    Returns: 
        On Success: (list of dictionaries, none)
        On Failure: (None, "Weather API Failed")

    Thoughts for V2:
        
        Should the URLs for API calls be stored as global variables rather than function specific?
        This function seems pretty specific and "separate". I'm not sure I could seperate concerns further. 

    """
    logging.info(f"Getting Weather for {latitude}, {longitude}, and {len(dates)} date ranges.")
    url = "https://archive-api.open-meteo.com/v1/archive"
    weather = []
    for start_date, end_date in dates:
        params = {
            "latitude" : latitude, 
            "longitude" : longitude, 
            "start_date" : start_date, 
            "end_date" : end_date,
            "daily" : "temperature_2m_max,temperature_2m_min,precipitation_sum,weather_code"         
        }
        data, error = safe_api_call(url, params=params, timeout=10)
        if error:
           logging.error(f"Weather API call failed for {start_date} to {end_date}: {error}")
           return None, "Weather API Call Failed"
        weather.append(data)
    logging.info(f"Weather successfully retrieved for {latitude}, {longitude}, {len(dates)} date ranges.")
    return weather, None

def get_weather_data(latitude, longitude, dates, api_call_list, connection):
    """
    Takes one of two actions: 
        If there is no API_list, it will call read_from_database for the given dates, latitude, longitude. It will sort the database
        data by date order.
        If there is an API_list, it will call read_from_database unless there are no dates to call, call convert_db_data, then call get_weather. 
        It will join the database data to the api_results data and sort them by date order. 
    
    Args:
        latitude: latitude coordinates created by geo_convert string
        longtidue: longitude coordinates created by geo_convert string
        dates: list of dates in format YYYY-MM-DD string
        api_call_list: list of dates not found in the database in format YYYY-MM-DD string
        connection: sqllite3 database connection
    
     Returns:
        Branch 1:
            On Success: (weather, error)
            On Failure: (None, "db_error")
        Branch 2: 
            On Success: (weather, error)
            On Failure: (None, error)
    
    Thoughts for V2:

        This is a messy function. It can almost certainly be broken down into smaller functions. One clear place for 
        optimization is that on both branches, data is converted and sorted. That could likely be one function.
        The branch is not good. There's too much complexity within each branch. Each branch could likley be a function, 
        simplifying down the overall function to either call one or another function depending on API_call_list.
        
    """
    
    logging.info(f"Get weather data started for Lat:{latitude}, Lon:{longitude}, for {len(dates)} number of dates, with API:{len(api_call_list)} and connection {bool(connection)}")

    if not api_call_list:
        try:
            db_data = read_from_database(latitude, longitude, dates, connection)
            logging.info(f"Database read with {len(db_data)} results.")
        except sqlite3.OperationalError:
            logging.error(f"Database read failed.")    
            return None, "db_error"
        weather = convert_db_data(db_data)
        weather = sorted(weather, key=lambda x: x["daily"]["time"][0])
        error = 0
        return weather, error
    else:
        try:
            db_data = read_from_database(latitude, longitude, dates, connection)
            logging.info(f"Database read with {len(db_data)} results.")
        except sqlite3.OperationalError:
            logging.error(f"Database read failed.")    
            return None, "db_error"
        db_data_converted = convert_db_data(db_data)
        api_results, error = get_weather(latitude, longitude, api_call_list)
        if error: 
                return None, error
        if db_data_converted:
            weather = api_results + db_data_converted
        else:
            weather = api_results
        weather = sorted(weather, key=lambda x: x["daily"]["time"][0])
        return weather, error


##Data Conversion

def date_converter(start_date, end_date):
    """
    Converts start_date and end_date range into 10 years of that same range 
    in the format required by the Open-Meteo weather API: string YYYY-MM-DD. Appends this to the dates list
    as tuples (s_full_date, e_full_date).

    Args:
        start_date: variable created by combining user input start day and start month string MM-DD
        end_date: variable created by combining user input end day and end month string MM-DD
    
    Returns:
        Dates, a list of tuples (s_full_date, e_full_date)
    
    Thoughts for V2:
        This is a pretty "separated" function. It's hard to see how I might optimize it. However, I want to keep
        an eye on the "date" system in this entire function, because there is redundancy. I don't think it's this function
        but none the less I need to flag this for comparison to the other less official moments of "date conversion" and figure
        out if everything that builds start and end dates is necessary or not.

    """
    logging.info(f"Converting dates for {start_date} and {end_date}")
    dates = []
    current_year = datetime.now().year
    for years_ago in range(10):
        year = current_year - years_ago
        s_full_date = f"{year}-{start_date}"
        e_full_date = f"{year}-{end_date}"
        dates.append((s_full_date, e_full_date))
    return dates
   
def code_converter(wc):
    """
    Converts the weather code from the API response into a string

    Args:
        wc: int
    
    Returns:
        wc: string
    
    Thoughts for V2:
        Simple function, not much to optmize, but I do have one thought. It shouldn't both take and return WC as a variable. 
        They should have distinct names to avoid possible confusion. Now, I'll need to look at this closer and assess if that's
        really a risk, but it seems like a good practice. 

    """
    if wc in [51, 53, 55, 61, 63, 65, 80, 81, 82, 56, 57, 66, 67]: #API Rain Codes
        wc = "Rain"
    elif wc in [71, 73, 75, 77, 85, 86]: #API Snow Codes
        wc = "Snow"
    elif wc in [0, 1]: #API Sun Codes
        wc = "Sunny"
    elif wc in [2, 3, 45, 48]: #API Cloudy or Partly Cloudy codes
        wc = "Cloudy"
    else:
        wc = "Unknown"
    return wc

def convert_db_data(db_data):
    """
    Converts the database data structure to match the Open-Meteo API call response data.

    Args:
        db_data: results of calling read_from_database. List of lists, where each inner list contains tuples (date, lat, lon, high_temp, low_temp, weather_code) each
        representing weather for a given date and location.
    
    Returns:
        weather: a list 
            Data Structure:
                [
                    { #one dictionary per year
                        "daily": {
                            "time": [list of date strings],
                            "temperature_2m_max": [list of int temperature highs],
                            "temperature_2m_min": [list of int temperature lows],
                            "weather_code": [list of ints]
                            }
                        }
                    ]
    
    Thoughts on V2:
        The only thoughts on this are vague, but it seems like maybe I could incorporate this into the read_data_base pull
        automatically. I'm not sure - does that violate separation of concerns? Maybe, but they're also so integrally tied to
        eachother. I don't know. This would be a significant structural change and I'd need to think through how it impacts the process.
        I could also consider reversing the flow: I could convert the API data upon receipt to match the database data. There's an elegance
        to that: data comes in and gets immediately transformed to suit our system. 

    """
    
    weather = []
    for year_data in db_data:
        date = []
        high_temp = []
        low_temp = []
        w_c = []
        daily = {
           "time": date,
           "temperature_2m_max": high_temp,
           "temperature_2m_min": low_temp,
           "weather_code": w_c 
        }
        year = {
            "daily" : daily
        }
        for day in year_data:
            date.append(day[0])
            high_temp.append(day[3])
            low_temp.append(day[4])
            w_c.append(day[5])
        if year["daily"]["time"]: #Confirms the database had data for that date before appending.
            weather.append(year)
    return weather

def date_calculator(dates):
    start_date, end_date = dates[0]
    start_date = datetime.strptime(start_date, "%Y-%m-%d").date()
    end_date = datetime.strptime(end_date, "%Y-%m-%d").date()
    date_span = end_date - start_date
    days = date_span.days
    total_days = days + 1
    return total_days


##Database
        
def read_from_database(latitude, longitude, dates, connection):
    cursor = connection.cursor()
    db_data = []
    for start_date, end_date in dates:
        cursor.execute("""
            SELECT date, lat, lon, high_temp, low_temp, weather_code 
            FROM weather           
            WHERE lat=? AND lon=? AND date >= ? AND date <= ?
            ORDER BY date
        """, (latitude, longitude, start_date, end_date))
        results = cursor.fetchall()
        db_data.append(results)
    return db_data
        
def write_to_database(weather, connection, latitude, longitude):
    logging.info(f"Attempting write to database.")
    cursor = connection.cursor()
    for year in weather:
        time_stamp = datetime.now().isoformat()
        dates = year["daily"]["time"]
        temp_highs = year["daily"]["temperature_2m_max"]
        temp_lows = year["daily"]["temperature_2m_min"]
        weather_codes = year["daily"]["weather_code"]    
        for date, temp_high, temp_low, weather_code in zip(dates, temp_highs, temp_lows, weather_codes):
            cursor.execute("""
                INSERT OR REPLACE INTO weather (lat, lon, date, high_temp, low_temp, weather_code, cached_at)
                VALUES (?,?,?,?,?,?,?)""",
                (latitude, longitude, date, temp_high, temp_low, weather_code, time_stamp)
            )
    connection.commit()
    print(f"API Coords: lat={latitude}, lon={longitude}")
       
def check_database(connection, latitude, longitude, dates):
    logging.info(f"Attempting check database.")
    cursor = connection.cursor()
    total_days = date_calculator(dates)
    api_call_list = []
    try:
        for start_date, end_date in dates:
            cursor.execute("""
                SELECT date, lat, lon
                FROM weather
                WHERE lat=? AND lon=? AND date >= ? AND date <= ?
                ORDER BY date                         
                """, (latitude, longitude, start_date, end_date))
            results = cursor.fetchall() 
            print(f"Date range: {start_date} to {end_date}, Results: {len(results)}, Expected: {total_days}")
            if not len(results) == total_days:
                api_call_list.append((start_date, end_date))
        return api_call_list, None
    except sqlite3.OperationalError:
        return None, "Check database error."
    

def create_or_connect_database():
    connection = sqlite3.connect("weather.db")
    cursor = connection.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS weather (
            lat REAL,
            lon REAL,
            date TEXT,
            high_temp REAL,
            low_temp REAL,
            weather_code INT,
            cached_at TEXT,
            PRIMARY KEY (lat, lon, date)
        )
    """)
    connection.commit()
    return connection


##UI

def table(weather, new_window):
    for year_data in weather:
        table = ttk.Treeview(new_window, columns=("Date", "Temp High","Temp Low", "Weather"), show="headings") 
        table.pack()
        table.heading("Date", text="Date")
        table.heading("Temp High", text="Temp High")
        table.heading("Temp Low", text="Temp Low")
        table.heading("Weather", text="Weather")
        date = year_data["daily"]["time"] 
        temperature_high = year_data["daily"]["temperature_2m_max"] 
        temperature_low = year_data["daily"]["temperature_2m_min"] 
        weather_code = year_data["daily"]["weather_code"]
        for day, high, low, wc in zip(date, temperature_high, temperature_low, weather_code): 
            cc = code_converter(wc)
            table.insert(parent='', index="end", values=(day, high, low, cc))






















"""
def change_api_code():
    #this function will change the API call for get weather OR
    #perhaps it's better to have this function "determine" which
    # API function to use - we could construct a separate get-weather
    # api that is used when the data is present and have a boolean
    # track to guide us to whichever one we need.
"""
   




















"""
def main():
    location_state, location_city, start_date, end_date = get_user_input()
    latitude, longitude = geo_convert(location_state, location_city)
    dates = date_converter(start_date, end_date)
    weather = get_weather(latitude, longitude, dates)
    weather_counts = precipitation(weather)
    print(f"Rainy Days: {weather_counts[0]}\nSnowy Days: {weather_counts[1]}\nSunny Days: {weather_counts[2]}\nCloudy Days: {weather_counts[3]}\nUnknown Days: {weather_counts[4]}")

if __name__ == "__main__":
    main()
    
"""

""""
def get_user_input():
    state = input("Enter state: ")
    city = input("Enter City: ")
    start_date = input("Enter start date DD/MM: ")
    date_span = input("Is the end date different from the start date? Y or N: ")
    if date_span == "Y":
        end_date = input("Enter end date DD/MM: ")
    else:
        end_date = None
    return state, city, start_date, end_date
"""


"""
    year_1_high = weather[0]["daily"]["temperature_2m_max"]
    year_2_high = weather[1]["daily"]["temperature_2m_max"]
    year_3_high = weather[2]["daily"]["temperature_2m_max"]
    year_1_low = weather[0]["daily"]["temperature_2m_min"]
    year_2_low = weather[1]["daily"]["temperature_2m_min"]
    year_3_low = weather[2]["daily"]["temperature_2m_min"]
    three_year_high = max(year_1_high + year_2_high + year_3_high)
    three_year_low = min(year_1_low + year_2_low + year_3_low)
"""

"""
def precipitation_10_years(weather):
    rainy_days = 0
    snowy_days = 0
    sunny_days = 0
    cloudy_days = 0
    unknown_day = 0
    for year_data in weather:
        weather_codes = year_data["daily"]["weather_code"]
        for code in weather_codes:
            if code in [51, 53, 55, 61, 63, 65, 80, 81, 82, 56, 57, 66, 67]:
                rainy_days += 1
            elif code in [71, 73, 75, 77, 85, 86]:
                snowy_days += 1
            elif code in [0, 1]:
                sunny_days += 1
            elif code in [2, 3, 45, 48]:
                cloudy_days += 1
            else:
                unknown_day += 1
    weather_types_10yr = [rainy_days, snowy_days, sunny_days, cloudy_days, unknown_day]
    return weather_types_10yr

def precipitation_5_years(weather):
    rainy_days = 0
    snowy_days = 0
    sunny_days = 0
    cloudy_days = 0
    unknown_day = 0
    for year_data in weather[0:5]:
        weather_codes = year_data["daily"]["weather_code"]
        for code in weather_codes:
            if code in [51, 53, 55, 61, 63, 65, 80, 81, 82, 56, 57, 66, 67]:
                rainy_days += 1
            elif code in [71, 73, 75, 77, 85, 86]:
                snowy_days += 1
            elif code in [0, 1]:
                sunny_days += 1
            elif code in [2, 3, 45, 48]:
                cloudy_days += 1
            else:
                unknown_day += 1
    weather_types_5yr = [rainy_days, snowy_days, sunny_days, cloudy_days, unknown_day]
    return weather_types_5yr

def weather_minmax(weather):
    temp_high_list = []
    temp_low_list = []
    for year_data in weather[:5]:
        temperature_high = year_data["daily"]["temperature_2m_max"]
        temperature_low = year_data["daily"]["temperature_2m_min"]
        for temp_high in temperature_high:
            temp_high_list.append(temp_high)
        for temp_low in temperature_low:
            temp_low_list.append(temp_low)
    return temp_high_list, temp_low_list   

"""