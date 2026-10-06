import weatherappbackV2
import api


def check_table(connection):
    """
    Verifies that the expected 'weather_data' table exists in the database.

    Runs a SELECT EXISTS query against the information_schema catalog. If the
    table is missing, raises immediately so the problem surfaces at startup
    rather than later when a query unexpectedly fails.

    Args:
        connection: Active psycopg2 database connection.

    Raises:
        RuntimeError: If the 'weather_data' table does not exist.
    """
    cursor = connection.cursor()
    # information_schema.tables is a built-in catalog listing every table.
    # SELECT EXISTS(...) returns a single boolean row: True if the inner query
    # found a match, False otherwise — a cheap way to test for existence.
    cursor.execute("""
                   SELECT EXISTS(
                   SELECT 1
                   FROM information_schema.tables
                   WHERE table_Name = 'weather_data'
                   );
                   """)
    exists = cursor.fetchone()[0]
    if not exists:
        raise RuntimeError("Table weather_data not found")


def connect_to_database():
    """
    Opens a connection to the PostgreSQL 'weather_app' database and confirms
    the required table is present.

    Returns:
        connection: An active psycopg2 connection, guaranteed to have the
                    'weather_data' table (check_table runs before returning).

    Raises:
        psycopg2.OperationalError: If the connection itself fails (re-raised
                                   after logging).
        RuntimeError: If the connection succeeds but the table is missing
                      (propagated from check_table).
    """
    logging.info("Attempting database connect")
    try:
        connection = psycopg2.connect(
            host="localhost",
            database="weather_app",
            user="postgres",
            password="AML3664179!"

        )
    except psycopg2.OperationalError as e:
        # Log the specific failure for debugging, then re-raise so the caller
        # knows the connection could not be established.
        logging.error(f"Database connection failed: {e}")
        raise
    # Only reached if the connection succeeded; fail fast if the schema is wrong.
    check_table(connection)
    return connection


## Checking Database

def date_calculator(span):
    """
    Calculates the number of days in a date range, inclusive of both endpoints.

    Args:
        span (tuple): A (start_date, end_date) tuple with dates as "YYYY-MM-DD" strings.

    Returns:
        int: The number of days in the range, inclusive.

    Thoughts for V2:
        Consider validating that start_date comes before end_date.
    """
    # strptime parses the string into a datetime object so the two dates can be
    # subtracted. Subtracting datetimes yields a timedelta; .days is the whole-day
    # difference. The +1 makes the count inclusive of both endpoints.
    d1 = datetime.strptime(span[0], "%Y-%m-%d")
    d2 = datetime.strptime(span[1], "%Y-%m-%d")
    days_span = (d2 - d1).days + 1
    return days_span


def build_api_list(date_list, db_data):
    """
    Identifies which date ranges are missing complete data in the database.

    Compares the number of days stored in the database for each year against
    the expected number of days in that year's date range. If there is a 
    mismatch, the full date range for that year is flagged for an API call.

    Args:
        date_list (list): List of (start_date, end_date) tuples, one per year,
                          with dates as "YYYY-MM-DD" strings.
        db_data (dict): Database results grouped by year. See build_db_data().

    Returns:
        list: A list of (start_date, end_date) tuples representing years that
              need to be fetched from the API.
   
    """
    api_list = []
    for span in date_list:
        days_span = date_calculator(span)
        YYYY = span[0][0:4]
        # .get(YYYY, []) returns an empty list if this year has no stored data,
        # so a completely missing year cleanly counts as 0 days present.
        database_days = db_data.get(YYYY, [])
        # If the stored day count doesn't match the expected count, treat the
        # whole year as needing a fresh fetch (rather than trying to patch gaps).
        if len(database_days) != days_span:
            api_list.append(span)
    return api_list


def build_db_data(results):
    """
    Transforms raw database rows into a dictionary grouped by year.

    Args:
        results (list): A flat list of database row tuples in the format
                        (date, lat, lon, temp_high, temp_low, weather, cached_at).

    Returns:
        dict: Keys are 4-digit year strings (e.g. "2024"). Values are lists of
              (date, temp_high, temp_low, weather) tuples for that year.
   
    """
    db_data = {}
    for day in results:
        # Pull only the fields we need by column index. Against the table
        # schema (date, lat, lon, temp_high, temp_low, weather, cached_at):
        #   day[0] = date, day[3] = temp_high, day[4] = temp_low, day[5] = weather.
        # lat/lon (indices 1, 2) and cached_at (index 6) are intentionally dropped.
        date = day[0]
        temp_high = day[3]
        temp_low = day[4]
        weather = day[5]
        day = (date, temp_high, temp_low, weather)
        year = day[0][0:4]
        # Create the year's list the first time we encounter it, then append.
        if year not in db_data:
            db_data[year] = []
        db_data[year].append(day)
    return db_data 


def pull_results(date_list, lat, lon, connection):
    """
    Queries the database for all stored weather records matching the location
    and date ranges provided.

    Args:
        date_list (list): List of (start_date, end_date) tuples, one per year,
                          with dates as "YYYY-MM-DD" strings.
        lat (float): Latitude of the location.
        lon (float): Longitude of the location.
        connection: Active psycopg2 database connection.

    Returns:
        list: A flat list of all matching database row tuples across all years.

    """
    cursor = connection.cursor()
    # Round to 2 decimals so these match the precision stored in the table
    # (lat numeric(5,2), lon numeric(6,2)); otherwise equality checks would miss.
    lat = round(lat, 2)
    lon = round(lon, 2)
    pull_results = []
    for start_date, end_date in date_list:
        # %s placeholders let psycopg2 safely substitute values (preventing SQL
        # injection). The tuple below fills them in positional order.
        cursor.execute("""
            SELECT *
            FROM weather_data
            WHERE lon = %s and lat = %s and date >= %s and date <= %s
         """, (lon, lat, start_date, end_date))
        results = cursor.fetchall()
        # extend (not append) flattens each year's rows into one combined list.
        pull_results.extend(results)
    return pull_results


def check_database(date_list, lat, lon, connection):
    """
    Checks the database for existing weather data and identifies gaps.

    Orchestrates the database checking workflow: pulls raw results, organizes
    them by year, and determines which years need to be fetched from the API.

    Args:
        date_list (list): List of (start_date, end_date) tuples, one per year,
                          with dates as "YYYY-MM-DD" strings.
        lat (float): Latitude of the location.
        lon (float): Longitude of the location.
        connection: Active psycopg2 database connection.

    Returns:
        tuple:
            db_data (dict): Weather data grouped by year. Empty dict if no
                            data exists. See build_db_data().
            api_list (list): Date ranges needing an API call. Empty list if
                             database is complete.
    """
    results = pull_results(date_list, lat, lon, connection)
    db_data = build_db_data(results)
    api_list = build_api_list(date_list, db_data)
    return db_data, api_list