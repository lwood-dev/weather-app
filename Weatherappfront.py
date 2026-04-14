"""
Front end user-interface for the Weather Application. Handles user data entry.
Interfaces with WeatherApp.py for all backend logic.
"""

import tkinter as tk
from tkinter import ttk
from tkinter import messagebox
import WeatherApp
import logging

logging.basicConfig(
    filename="weather_app.log",
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

logging.info("Weather app started.")

connection = WeatherApp.create_or_connect_database()

window=tk.Tk()
window.title("Weather Search App")
window.geometry("500x500")

label = tk.Label(window, text="Weather History App")
label.grid(row=0, column=2)

weather_data = None

states = [
    "Alabama", "Alaska", "Arizona", "Arkansas", "California",
    "Colorado", "Connecticut", "Delaware", "Florida", "Georgia",
    "Hawaii", "Idaho", "Illinois", "Indiana", "Iowa",
    "Kansas", "Kentucky", "Louisiana", "Maine", "Maryland",
    "Massachusetts", "Michigan", "Minnesota", "Mississippi", "Missouri",
    "Montana", "Nebraska", "Nevada", "New Hampshire", "New Jersey",
    "New Mexico", "New York", "North Carolina", "North Dakota", "Ohio",
    "Oklahoma", "Oregon", "Pennsylvania", "Rhode Island", "South Carolina",
    "South Dakota", "Tennessee", "Texas", "Utah", "Vermont",
    "Virginia", "Washington", "West Virginia", "Wisconsin", "Wyoming"
]

months = [str(i).zfill(2) for i in range (1,13)] # Zero-pads integers to 2 digits (1 -> 01) for consistent date formatting. 
months_w_28 = ["02"] # February - months with 28 days - leap year not incorporated
months_w_30 = ["04","06","09","11"] # Months with 30 days
months_w_31 = ["01","03","05","07","08","10","12"] # Months with 31 days
dates_28 = [str(i).zfill(2) for i in range (1,29)]
dates_30 = [str(i).zfill(2) for i in range (1,31)]
dates_31 = [str(i).zfill(2) for i in range (1,32)]

correct_dates = {
    "months_w_28": dates_28,
    "months_w_30": dates_30,
    "months_w_31": dates_31
} # Maps month-length categories to their valid day ranges

def closure(combobox_month, combobox_day):
    """
    Closure function for creating a function which takes the month user-input and selects a list of calendar days (numerical) with the appropriate number of days corresponding to that month.  

    Args:
        combobox_month: tkinter ttk.combobox widget. Dropdown for selecting and storing the user-input month. 
        combobox_day: tkinter ttk.combobox widget. Dropdown for selecting and storing the user-input day.
            
    Returns:
        date_choice: a function date_choice using the input combobox_month and combobox_day 
    
    V2 Thoughts:
        This is an interesting one. In a way, I made this as a challenge to myself - it was suggested as a potential solution and it looked difficult. I'm glad I did it and learned the concept. 
        With that said, it's kind of a silly use of a closure. There's only two instances where I need the date_choice function. In reality, I probably should have just written to two functions. This is overengineered.
        But, at the same time, since it's done, I am resistant to remove it. I don't think it's doing any damage as is or is "improved" by scrapping it to write two new functions. I just think that, were I starting over, 
        I wouldn't utilize a closure again for this purpose. Whether this stays or goes may be a question that gets answered deeper into the refactor process. 
    

    """
    def date_choice(event):
        """
        When a month is chosen by the user, the corresponding date drop-down updates to reflect the appropriate number of days. 

        Args:

            event: created by tkinter ttk combobox_select. Not used in the function, but required to be carried in. 
        
        Returns:
            None
        
        V2 Thoughts:
            See V2 thoughts for closure().

         
        """
        trigger = combobox_month.get()
        if trigger in months_w_28:
            combobox_day["values"]=correct_dates["months_w_28"]
        if trigger in months_w_30:
            combobox_day["values"]=correct_dates["months_w_30"]
        if trigger in months_w_31:
            combobox_day["values"]=correct_dates["months_w_31"]
    return date_choice

def date_validation():
    """
    Validates user input data for start month, start day, end month, and end day. Tests if the end_date is after the start_date. 

    Args:
        None
    
    Returns:
       bool: True if all fields are filled and end_date is on or after start_date, False otherwise

    V2 Thoughts:
        Each of the date functions needs to be assessed. There is a flaw/redudancy in the date data flow. Looking at this function, though, I think it's probably fine. It's purpose isn't to shape the data, just to validate that data was entered.
        It seems to do its job. However, after the if-statement could conceivably be it's own function. And, in fact, if the section checking the chronology was it's own function, it would be a part of the overall issue with redudant or differing "creation" of start/end dates. 
        I could (and likely will) have a separate, definitive function creating the "start date" and "end date" in an official format and that could be fed into the new function built from the second half of this function. This would also give me an opportunity to FIRST test that the 
        data was entered, then assemble the data in the "official" start/end date structure, then test that the start/end date are sequential.
        Ok,so this one actually could use some work. 

        From Claude: 
        This function accesses the combobox widgets directly by name rather than 
        accepting them as arguments, creating a hidden dependency on global widget 
        names. In v2, consider passing them as arguments to make the function 
        more portable and explicit about its dependencies.

    """
    start_month = start_date_month_select.get()
    start_day = start_date_day_select.get()
    end_month = end_date_month_select.get()
    end_day = end_date_day_select.get()
    if not start_month or not start_day or not end_month or not end_day:
        return False
    start_date = start_month + start_day
    end_date = end_month + end_day
    return end_date >= start_date  

def display_results(weather):
    """
    Creates and structures a new tkinter scrollable results window to display for the weather data results.

    Args:
        weather: weather data as generated by get_weather_data()

    Returns:
        None
    
    V2 Thoughts:

    I don't have much to change here unless I wanted to add some kind of new feature. It's an effective UI and doesn't seem to break or create errors on use. On the other hand, if the weather data structure changes,
    I might need to address changes here. Will need to keep an eye on it - though I think most of that will come back to table()

    """
    new_window = tk.Toplevel()
    new_window.title("Weather Results")
    new_window.geometry("900x700")
    canvas = tk.Canvas(new_window, width=800, height=600)
    frame = tk.Frame(canvas)
    canvas.create_window((0, 0), window=frame, anchor="nw")
    scrollbar = ttk.Scrollbar(new_window, orient="vertical", command=canvas.yview)
    canvas.configure(yscrollcommand=scrollbar.set)
    canvas.pack(side="left", fill="both", expand=True)
    scrollbar.pack(side="right", fill="y")
    WeatherApp.table(weather, frame)
    canvas.update_idletasks()
    canvas.configure(scrollregion=canvas.bbox("all"))
    frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
    
def submit_data():
    """
    The central submit handler for the application. Coordinates the full 
    data retrieval workflow: validates user input, resolves the location 
    to coordinates, checks the database for cached data, fetches any 
    missing years from the API, writes new data back to the database, 
    and calls display_results() to render the final table.

    If any step fails, shows an appropriate error dialog and returns early.

    Args:
        None
    
    Returns:
        None

    Note:
        Reads directly from global Tkinter widget variables for all user 
        input. Also writes to the global weather_data variable via 
        display_results(). See date_validation() for related Note.
    
    V2 Thoughts:
        This function needs a lot of work, but exactly what work depends on how the overall program
        is restructured. With that said, there are some glaring issues. The "date problem' raises it's head again here. There should be on function creating an official date format.
        Although this function does an OK job at mainly calling functions to serve it, it does look like certain parts of this function
        could potentially be broken off into smaller functions. I'l lneed to look closely at that. 
        I expect that this function will be one of the final reworks of V2. With that said, though everything else needs to be written before this function can be finalized, 
        it needs to be kept in at the forefront of mind during the planning stage.   
    """
    global weather_data
    if not date_validation():
        logging.warning(f"Date validation failed: start={start_date_month_select.get()}{start_date_day_select.get()}, end={end_date_month_select.get()}{end_date_day_select.get()}")
        messagebox.showerror("Date Error", "Please select valid start and end dates.")
        return 
    location_state = state_select.get()
    location_city = city_select.get()
    if location_state == "Select a State" or not location_city:
        logging.warning(f"Missing location: state={location_state}, city={location_city}")
        messagebox.showerror("Location Error","Input error for State or City")
        return
    start_date = start_date_month_select.get()+ "-" +start_date_day_select.get()
    end_date = end_date_month_select.get()+ "-" +end_date_day_select.get()
    latitude, longitude, error = WeatherApp.geo_convert(location_state, location_city)
    if error:
        messagebox.showerror("Location Error", "There was an error with the location. It may be entered incorrectly or unavailable.")
        return
    dates = WeatherApp.date_converter(start_date, end_date)
    api_call_list, error = WeatherApp.check_database(connection, latitude, longitude, dates)
    if error:
        logging.error(f"Database check failed.")
        messagebox.showerror("Database Error","Failure to read the database.")
        return
    logging.info(f"Database checked successfully. Returned {len(api_call_list)} years needed for API call.")
    weather, error = WeatherApp.get_weather_data(latitude, longitude, dates, api_call_list, connection)
    if error:
        logging.error("Failed to get weather data.")
        messagebox.showerror("Data Retrieval Failed", "There was an error getting the weather data.")
        return
    logging.info(f"get_weather_data completed successfully - {len(weather)} years assembled.")
    try:
        WeatherApp.write_to_database(weather, connection, latitude, longitude)
        logging.info("Data written to dattabase.")
    except Exception as e:
        logging.error(f"Failed to write to database - cache not saved: {e}")    
    display_results(weather)
    
    
##Creation Phase

state_label = tk.Label(window, text="Choose a State")
state_select = ttk.Combobox(window, values=states, state="readonly")
city_label = tk.Label(window, text="Enter a City")
city_select = tk.Entry(window, text="Enter a City")
start_date_month_label = tk.Label(window, text="Choose a Start Date") 
start_date_month_select = ttk.Combobox(window, values=months, state="readonly")
start_date_day_label = tk.Label(window)
start_date_day_select = ttk.Combobox(window, values=[], state="readonly")
end_date_month_label = tk.Label(window, text="Choose an End Date")
end_date_month_select = ttk.Combobox(window, values=months, state="readonly")
end_date_day_label = tk.Label(window)
end_date_day_select = ttk.Combobox(window, values=[], state="readonly")
submit_button = tk.Button(window, text="Get Weather")

# Configure Phase

start_date_handler = closure(start_date_month_select, start_date_day_select)
start_date_month_select.bind("<<ComboboxSelected>>", start_date_handler)

end_date_handler = closure(end_date_month_select, end_date_day_select)
end_date_month_select.bind("<<ComboboxSelected>>", end_date_handler)

submit_button.config(command=submit_data)

# Layout Phase

state_label.grid(row=2, column=1, padx=(20,0))
state_select.grid(row=3, column=1, padx=(20,0))
state_select.set("Select a State")
city_label.grid(row=2, column=2)
city_select.grid(row=3, column=2)
start_date_month_label.grid(row=6, column=1)
start_date_month_select.grid(row=7, column=1)
start_date_day_label.grid(row=6, column=2)
start_date_day_select.grid(row=7, column=2)
end_date_month_label.grid(row=8, column=1)
end_date_month_select.grid(row=9, column=1)
end_date_day_label.grid(row=8, column=2)
end_date_day_select.grid(row=9, column=2)
submit_button.grid(row=10, column=2)

window.mainloop()

connection.close()