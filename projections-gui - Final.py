import pandas as pd
import tkinter as tk
from tkinter import filedialog, messagebox
import os

def adjust_weekdays(day):
    # Adjust the day of the week to start from Wednesday
    week_order = {'Wednesday': 0, 'Thursday': 1, 'Friday': 2, 'Saturday': 3, 'Sunday': 4, 'Monday': 5, 'Tuesday': 6}
    return week_order.get(day, day)

def process_file(file_path, period):
    # Load the CSV file
    df = pd.read_csv(file_path)

    # Extract relevant columns (date and sales_amount)
    df = df[['TextBox4', 'TextBox3']]

    # Rename columns for easier access
    df.columns = ['date', 'sales_amount']

    # Convert 'date' to datetime format
    df['date'] = pd.to_datetime(df['date'], format='%A, %B %d, %Y', errors='coerce')

    # Remove rows with invalid dates
    df = df.dropna(subset=['date'])

    # Convert 'sales_amount' to numeric by removing dollar sign and commas
    df['sales_amount'] = df['sales_amount'].replace('[\$,]', '', regex=True).astype(float)

    # Filter data for the last 4 weeks (28 days)
    end_date = df['date'].max()
    start_date = end_date - pd.Timedelta(days=28)
    df_last_4_weeks = df[(df['date'] >= start_date) & (df['date'] <= end_date)]

    # Add a column for the day of the week adjusted to start on Wednesday
    df_last_4_weeks['day_of_week'] = df_last_4_weeks['date'].dt.day_name()
    df_last_4_weeks['day_order'] = df_last_4_weeks['day_of_week'].apply(adjust_weekdays)

    # Aggregate sales by day of the week
    df_daily_sales = df_last_4_weeks.groupby(['day_of_week', 'day_order'])['sales_amount'].mean().reset_index()

    # Sort the days of the week from Wednesday to Tuesday
    df_daily_sales = df_daily_sales.sort_values('day_order')

    # Prepare the predictions for next week and round to 2 decimal places
    predicted_sales_next_week = df_daily_sales[['day_of_week', 'sales_amount']].copy()
    predicted_sales_next_week.columns = ['Day of Week', f'Predicted {period} Sales']
    predicted_sales_next_week[f'Predicted {period} Sales'] = predicted_sales_next_week[f'Predicted {period} Sales'].round(2)

    return predicted_sales_next_week, end_date

def open_file_am():
    global am_sales_predictions, latest_date_am
    file_path = filedialog.askopenfilename(filetypes=[("CSV files", "*.csv")])
    if file_path:
        am_sales_predictions, latest_date_am = process_file(file_path, 'AM')

def open_file_pm():
    global pm_sales_predictions, latest_date_pm
    file_path = filedialog.askopenfilename(filetypes=[("CSV files", "*.csv")])
    if file_path:
        pm_sales_predictions, latest_date_pm = process_file(file_path, 'PM')

def submit_files():
    if am_sales_predictions is not None and pm_sales_predictions is not None:
        combined_predictions = pd.merge(am_sales_predictions, pm_sales_predictions, on="Day of Week", how='outer')
        
        # Determine the latest date between AM and PM data
        latest_date = max(latest_date_am, latest_date_pm)
        
        # Calculate the next Wednesday
        days_until_next_wednesday = (2 - latest_date.weekday() + 7) % 7  # Wednesday is day 2
        if days_until_next_wednesday == 0:
            days_until_next_wednesday = 7  # Ensure we go to the next Wednesday
        next_wednesday = latest_date + pd.Timedelta(days=days_until_next_wednesday)

        # Assign dates for the next week to the corresponding days
        next_week_dates = [(next_wednesday + pd.Timedelta(days=i)).strftime('%m/%d') for i in range(7)]
        day_order = ['Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday', 'Monday', 'Tuesday']
        date_mapping = dict(zip(day_order, next_week_dates))

        combined_predictions['Date'] = combined_predictions['Day of Week'].map(date_mapping)
        combined_predictions['Day with Date'] = combined_predictions['Day of Week'] + " " + combined_predictions['Date']

        # Sort by the correct order: Wednesday to Tuesday
        combined_predictions['day_order'] = combined_predictions['Day of Week'].apply(adjust_weekdays)
        combined_predictions = combined_predictions.sort_values('day_order')

        predictions_text = combined_predictions[['Day with Date', 'Predicted AM Sales', 'Predicted PM Sales']].to_string(index=False)
        messagebox.showinfo("Sales Predictions", predictions_text)

        # Save to a text file for printing
        with open("sales_predictions.txt", "w") as file:
            file.write(predictions_text)

    else:
        messagebox.showwarning("Warning", "Please select both AM and PM sales files.")

def print_predictions():
    if os.path.exists("sales_predictions.txt"):
        # Command to print the text file
        if os.name == 'nt':  # For Windows
            os.startfile("sales_predictions.txt", "print")
        else:
            os.system("lp sales_predictions.txt")
    else:
        messagebox.showwarning("Warning", "No predictions available to print. Please generate predictions first.")

# Initialize the global variables
am_sales_predictions = None
pm_sales_predictions = None
latest_date_am = None
latest_date_pm = None

# Set up the main application window
root = tk.Tk()
root.title("Sales Prediction")

# Create and place the buttons
btn_am = tk.Button(root, text="Select AM Sales CSV File", command=open_file_am)
btn_pm = tk.Button(root, text="Select PM Sales CSV File", command=open_file_pm)
btn_submit = tk.Button(root, text="Submit", command=submit_files)
btn_print = tk.Button(root, text="Print", command=print_predictions)

btn_am.pack(pady=10)
btn_pm.pack(pady=10)
btn_submit.pack(pady=10)
btn_print.pack(pady=20)

# Run the application
root.mainloop()
