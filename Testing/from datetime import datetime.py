from datetime import datetime
import sqlite3

def create_or_connect_database():
    connection = sqlite3.connect(":memory:")
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

def check_database(connection, latitude, longitude, dates):
    cursor = connection.cursor()
    total_days = date_calculator(dates)
    api_call_list = []
    #calculate the number of days between start and end date (inclusive)
    for start_date, end_date in dates:
        cursor.execute("""
            SELECT date, lat, lon
            FROM weather
            WHERE lat=? AND lon=? AND date >= ? AND date <= ?
            ORDER BY date                         
            """, (latitude, longitude, start_date, end_date))
        results = cursor.fetchall() 
        if not len(results) == total_days:
            api_call_list.append((start_date, end_date))
    return api_call_list
       
def date_calculator(dates):
    start_date, end_date = dates[0]
    start_date = datetime.strptime(start_date, "%Y-%m-%d").date()
    end_date = datetime.strptime(end_date, "%Y-%m-%d").date()
    date_span = end_date - start_date
    days = date_span.days
    total_days = days + 1
    return total_days

test_conn = create_or_connect_database()
test_cursor = test_conn.cursor()

# Test coordinates
test_lat = 40.7128
test_lon = -74.0060

# Insert COMPLETE data for 2024 (July 15-20 = 6 days)
test_cursor.execute("""
    INSERT INTO weather VALUES (?, ?, '2024-07-15', 85.5, 72.3, 1, '2024-01-01 10:00:00')
""", (test_lat, test_lon))

test_cursor.execute("""
    INSERT INTO weather VALUES (?, ?, '2024-07-16', 86.2, 73.1, 2, '2024-01-01 10:00:00')
""", (test_lat, test_lon))

test_cursor.execute("""
    INSERT INTO weather VALUES (?, ?, '2024-07-17', 87.1, 74.0, 1, '2024-01-01 10:00:00')
""", (test_lat, test_lon))

test_cursor.execute("""
    INSERT INTO weather VALUES (?, ?, '2024-07-18', 84.8, 71.5, 3, '2024-01-01 10:00:00')
""", (test_lat, test_lon))

test_cursor.execute("""
    INSERT INTO weather VALUES (?, ?, '2024-07-19', 83.9, 70.2, 2, '2024-01-01 10:00:00')
""", (test_lat, test_lon))

test_cursor.execute("""
    INSERT INTO weather VALUES (?, ?, '2024-07-20', 85.0, 72.8, 1, '2024-01-01 10:00:00')
""", (test_lat, test_lon))

# Insert INCOMPLETE data for 2023 (only 3 out of 6 days)
test_cursor.execute("""
    INSERT INTO weather VALUES (?, ?, '2023-07-16', 88.1, 75.2, 2, '2024-01-01 10:00:00')
""", (test_lat, test_lon))

test_cursor.execute("""
    INSERT INTO weather VALUES (?, ?, '2023-07-17', 89.3, 76.1, 1, '2024-01-01 10:00:00')
""", (test_lat, test_lon))

test_cursor.execute("""
    INSERT INTO weather VALUES (?, ?, '2023-07-20', 87.5, 74.8, 3, '2024-01-01 10:00:00')
""", (test_lat, test_lon))

# Commit all test data
test_conn.commit()

# Test dates (same date range for both years)
test_dates = [
    ("2024-07-15", "2024-07-20"),  # COMPLETE - should NOT be in api_call_list
    ("2023-07-15", "2023-07-20"),  # INCOMPLETE - SHOULD be in api_call_list
]

# Run the function
result = check_database(test_conn, test_lat, test_lon, test_dates)

# Display results
print(f"Expected days per year: {date_calculator(test_dates)}")
print(f"\nAPI call list: {result}")
print(f"Expected: [('2023-07-15', '2023-07-20')]")
print(f"\nTest {'PASSED ✓' if result == [('2023-07-15', '2023-07-20')] else 'FAILED ✗'}")

test_conn.close()