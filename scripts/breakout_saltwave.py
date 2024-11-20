import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.widgets import Cursor
from matplotlib.dates import num2date

# User-defined variables
file_path = 'AT200_013.xlsx'  # Replace with your actual file path
stn = 'station2'  # User-defined station name
loc = 'RL'  # User-defined location
initial_dump_number = 1  # User-defined initial dump number
date = ''  # Will be derived from the first timestamp of the subset data if left blank
sens = ''  # Will be derived from filename or metadata, if left blank

# Load metadata and data
df = pd.read_excel(file_path, header=None)
header_lines = 0
for index, row in df.iterrows():
    if pd.to_datetime(row, errors='coerce').notna().any():  # Check if row contains a datetime
        header_lines = index
        break

metadata = df.iloc[:header_lines]  # Extract metadata rows
df = pd.read_excel(file_path, skiprows=header_lines)  # Reload data with proper headers

# Ensure datetime column is parsed as datetime and naive
if 'DT' in df.columns:
    dt_col = 'DT'
elif 'DateTime' in df.columns:
    dt_col = 'DateTime'
else:
    raise ValueError("Expected datetime column not found. Please rename the datetime column or update the code.")
df[dt_col] = pd.to_datetime(df[dt_col]).dt.tz_localize(None)

# Get plot column
if 'EC.T' in df.columns:
    plot_col = 'EC.T'
elif 'EC.T(uS/cm)' in df.columns:
    plot_col = 'EC.T(uS/cm)'
else:
    raise ValueError("Expected plot column not found. Please rename the plot column or update the code.")

# Check if 'sens' is provided, else detect from filename or metadata
if not sens:
    if 'AT' in file_path:  # If filename contains ATXXX pattern
        sens = file_path.split('AT')[1][:4]  # Extract the ATXXX portion
    elif 'TM7.' in metadata.iloc[-1, 0]:  # Check metadata for TM7.XXX
        sens = 'TM7.' + metadata.iloc[-1, 0].split('TM7.')[1]  # Ensure TM7. part is included

# Determine date if not provided
if not date:
    date = df[dt_col].iloc[0].strftime('%Y%m%d')  # Use the first timestamp of the subset data

# Plot the time series
fig, ax = plt.subplots()
ax.plot(df[dt_col], df[plot_col], label=plot_col)
ax.set_xlabel('Time')
ax.set_ylabel(plot_col)
ax.set_title(f'{plot_col} Time Series')
ax.grid(True)
ax.legend()

# Set up the cursor widget for interactivity
cursor = Cursor(ax, useblit=True, color='red', linewidth=1)

# List to store clicked points
points = []
subset_times = []
dump_counter = initial_dump_number  # Initialize dump counter

# Event handler for click interaction
def on_click(event):
    global dump_counter  # Use global dump_counter to increment dump number

    if event.xdata is not None:  # Process only if there is a valid click
        # Convert xdata (numeric value) to a datetime object
        clicked_datetime = num2date(event.xdata)
        clicked_datetime_naive = clicked_datetime.replace(microsecond=0, tzinfo=None)

        # Find the closest timestamp in the DataFrame
        closest_idx = (df[dt_col] - clicked_datetime_naive).abs().argmin()
        closest_time = df.iloc[closest_idx][dt_col]
        subset_times.append(closest_time)

        # Get the corresponding y-value from the plot
        y_value = df.iloc[closest_idx][plot_col]

        points.append((event.xdata, y_value))  # Store x and the corresponding y-value
        ax.scatter(event.xdata, y_value, color='red')  # Scatter the point at (x, y)
        plt.draw()

        if len(points) % 2 == 0:  # Process after two clicks
            # Create a new DataFrame between the two selected timestamps
            subset_times.sort()
            new_df = df[(df[dt_col] >= subset_times[0]) & (df[dt_col] <= subset_times[1])]

            # Combine metadata and subset data (OLD WORKING STRUCTURE)
            output_df = pd.concat([metadata, new_df], ignore_index=True)
            
            # Save the combined DataFrame
            output_file = f"{stn}_{date}_dump{dump_counter}_{loc}_{sens}.xlsx"
            output_df.to_excel(output_file, index=False, header=False)  # Disable headers to match old behavior

            print(f'New dataframe saved as {output_file}')
            print(f"Dump {dump_counter} times: {subset_times}")
            dump_counter += 1  # Increment dump number for the next file

            points.clear()  # Reset points for the next dump selection
            subset_times.clear()  # Clear subset_times for the next dump selection

# Show the plot and wait for the user to click
fig.canvas.mpl_connect('button_press_event', on_click)

# Show the plot
plt.show()
