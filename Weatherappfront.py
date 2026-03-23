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

months = [str(i).zfill(2) for i in range (1,13)]
months_w_28 = ["02"]
months_w_30 = ["04","06","09","11"]
months_w_31 = ["01","03","05","07","08","10","12"]
dates_28 = [str(i).zfill(2) for i in range (1,29)]
dates_30 = [str(i).zfill(2) for i in range (1,31)]
dates_31 = [str(i).zfill(2) for i in range (1,32)]

correct_dates = {
    "months_w_28": dates_28,
    "months_w_30": dates_30,
    "months_w_31": dates_31
}

def closure(combobox_month, combobox_day):
    def date_choice(event):
        trigger = combobox_month.get()
        if trigger in months_w_28:
            combobox_day["values"]=correct_dates["months_w_28"]
        if trigger in months_w_30:
            combobox_day["values"]=correct_dates["months_w_30"]
        if trigger in months_w_31:
            combobox_day["values"]=correct_dates["months_w_31"]
    return date_choice

def date_validation():
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
    print(f"Geocoder coords: lat={latitude}, lon={longitude}")
    
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




"""
Old Code for the fork in Submit at the API_call_list/DB Data point: 
if not api_call_list:
        db_data = read_from_database(latitude, longitude, dates)
        weather = convert_db_data(db_data)
    if api_call_list:
        weather, error = WeatherApp.get_weather(latitude, longitude, api_call_list)
        if error:
            messagebox.showerror(error, "Failed to get weather")
            return
"""