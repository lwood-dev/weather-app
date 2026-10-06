from datetime import datetime, timedelta
from datetime import date
import requests
from tkinter import messagebox
import database
import api

# Cap the request window: 10 years × 30 days is already a large API pull,
# and no realistic user needs a longer seasonal window.
MAX_DATE_RANGE = timedelta(days=30)

#Classes

class Search:
    
    def __init__(self, city, state, start_date, end_date, connection):
        self.city = city
        self.state = state
        self.start_date = start_date
        self.end_date = end_date
        self.full_start = None
        self.full_end = None
        self.lat = None
        self.lon = None
        self.date_list = []
        self.api_call_list = []
        self.db_data = None
        self.weather_data = None
        self.connection = connection

    def transform_user_data(self):
        self.full_start, self.full_end = date_transformer(self.start_date, self.end_date)
        self.date_list = date_list_creator(self.full_start, self.full_end)
        self.lat, self.lon = api.call_coordinates_api(self.city, self.state)
        self.db_data, self.api_list = database.check_database(self.date_list, self.lat, self.lon, self.connection) 

    def fetch_weather(self):
        pass
    
#Data Processing Logic

def date_list_creator(full_start_date, full_end_date):
    """
    Expands a single date range into ten yearly ranges — the same calendar
    window for each of the last ten years.

    Given one "YYYY-MM-DD" start/end range, produces a range for the given year 
    and each of the nine years before it, keeping the month and day fixed
    while only the year changes. This is what lets the app compare the same
    seasonal window across a decade of historical weather.

    Args:
        full_start_date (str): Start date as "YYYY-MM-DD".
        full_end_date (str): End date as "YYYY-MM-DD".

    Returns:
        list: A list of 10 (start_date, end_date) tuples, one per year, most
              recent year first.
    """
    date_list = []
    for i in range(10):  # current year plus the nine preceding years
        start_YYYY = str(int(full_start_date[0:4])-i)
        end_YYYY = str(int(full_end_date[0:4])-i)
        full_start_date_final = start_YYYY + full_start_date[4:]
        full_end_date_final = end_YYYY + full_end_date[4:]
        date_list.append((full_start_date_final, full_end_date_final))
    return date_list

def date_span_check(start_str, end_str):
    """Parse and validate a date span from two ISO-format strings. Raise an error if the date span exceeds the MAX_DATE_RANGE. 

    Args:
        start_str: Start date as "YYYY-MM-DD".
        end_str: End date as "YYYY-MM-DD".

        
    Returns:
        Nothing

    Raises:
        ValueError if dates exceed MAX_RANGE_DATE. 
    
    """
    start = datetime.strptime(start_str, "%Y-%m-%d").date()
    end = datetime.strptime(end_str, "%Y-%m-%d").date()

    if end - start > MAX_DATE_RANGE:
        raise ValueError(f"Date span can not exceed {MAX_DATE_RANGE}")
        

def date_transformer(start_date, end_date, year=None):
    """
    Converts user-entered "MM-DD" dates into full "YYYY-MM-DD"

    Splits the month and day out of each "MM-DD" input, prepends the current
    year to form valid "YYYY-MM-DD" strings. Delegates to date_span_check to confirm whether a date exceeds
    the MAX_DATE_RANGE day span. if the end date falls before the start date, the range is treated as wrapping into the following year.

    Args:
        start_date (str): Start date as "MM-DD". (Must be zero padded)
        end_date (str): End date as "MM-DD". (Must be zero padded)
        year: YYYY int

    Returns:
        Tuple containing Strings of full dates in format "YYYY-MM-DD"

    Raises: 

        ValueError from date_span_check
    """
    # Slice month and day out of each "MM-DD" string:
    #   [0:2] -> month, [3:] -> day (index 2 is the "-" separator, skipped).
    start_month, start_day, end_month, end_day = start_date[0:2], start_date[3:], end_date[0:2], end_date[3:]
    if year is None:
        year = datetime.now().year
    current_year = str(year)
    end_year = current_year
    if start_date > end_date:
        end_year = str(year + 1)
    # Assemble "YYYY-MM-DD" strings by joining year, month, and day with dashes.
    full_start_date, full_end_date = current_year+"-"+start_month+"-"+start_day, end_year+"-"+end_month+"-"+end_day
    date_span_check(full_start_date, full_end_date)
    return full_start_date, full_end_date


def build_date_list(start_date, end_date):
    full_start_date, full_end_date = date_transformer(start_date, end_date)
    return date_list_creator(full_start_date, full_end_date)

