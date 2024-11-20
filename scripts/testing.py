import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.widgets import Cursor
from matplotlib.dates import num2date

# Step 1: Load the actual .xlsx file
def load_data(file_path):
    df = pd.read_excel(file_path)
    # Ensure 'DT' is parsed as datetime
    df['DT'] = pd.to_datetime(df['DT'])
    return df

# Step 2: Plot specified variable/column from the dataframe
def plot_variable(df, column_name):
    plt.plot(df['DT'], df[column_name], label=column_name)
    plt.xlabel('Time')
    plt.ylabel(column_name)
    plt.title(f'{column_name} Time Series')
    plt.grid(True)
    plt.legend()

# Step 3: Allow user to click on the plot and print xdata and ydata
def on_click(event, df):
    if event.xdata is not None and event.ydata is not None:
        # Print out the raw xdata and ydata from the click
        print(f"Clicked at x={event.xdata}, y={event.ydata}")
        
        # Convert the xdata to a datetime using num2date
        clicked_datetime = num2date(event.xdata)
        print(f"Clicked raw timestamp (numeric to datetime): {clicked_datetime}")

        # Ensure clicked_datetime is naive (remove timezone if it has one)
        if clicked_datetime.tzinfo is not None:
            clicked_datetime = clicked_datetime.replace(tzinfo=None)
        print(f"Naive clicked timestamp: {clicked_datetime}")

        # Trim the decimals (e.g., remove microseconds)
        clicked_datetime_trimmed = clicked_datetime.replace(microsecond=0)
        print(f"Trimmed clicked timestamp: {clicked_datetime_trimmed}")

        # Ensure df['DT'] is naive (remove timezone if it has one)
        df['DT'] = df['DT'].dt.tz_localize(None)

        # Find the closest timestamp in the dataframe
        closest_idx = (df['DT'] - clicked_datetime_trimmed).abs().argmin()
        closest_time = df.iloc[closest_idx]['DT']
        print(f"Closest datetime in dataframe: {closest_time}")

# Main function to execute the script
def interactive_plot(file_path, column_name):
    df = load_data(file_path)

    fig, ax = plt.subplots()
    plot_variable(df, column_name)

    # Set up the cursor widget for interactivity
    cursor = Cursor(ax, useblit=True, color='red', linewidth=1)
    
    # Lambda to pass the DataFrame as an argument to on_click
    fig.canvas.mpl_connect('button_press_event', lambda event: on_click(event, df))

    plt.show()

# Example usage
interactive_plot('AT200_013.xlsx', 'EC.T')  # Replace with your actual file path and column name
