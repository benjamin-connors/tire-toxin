import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.widgets import Cursor
from matplotlib.dates import num2date

# User-defined variables
file_path = 'AT200_013.xlsx'  # Replace with your actual file path
stn = 'stationAT'  # User-defined station name
loc = 'RL'  # User-defined location
initial_dump_number = 1  # User-defined initial dump number (dump number used for first dump in file)
date = ''  # Will be derived from the first timestamp of the subset data if left blank
sens = ''  # Will be derived from filename or metadata, if left blank

# Dynamically identify the first row containing a datetime value
data_preview = pd.read_excel(file_path, header=None)  # Read file without assuming column names
first_data_row = None  # Initialize variable for the first data row (the first row with datetime)

# Identify the first row containing a datetime value
for i, row in data_preview.iterrows():
    if pd.to_datetime(row, errors='coerce').notna().any():  # Check if any cell can be parsed as datetime
        first_data_row = i  # This row contains the first data
        break

if first_data_row is None:
    raise ValueError("No datetime values found in the file. Please check the file format.")

# Store metadata (all lines above column names) in a dataframe
metadata = data_preview.iloc[:first_data_row - 2]  # Metadata includes all rows above column names

# Load data with identified column names and skipping metadata rows
df = pd.read_excel(file_path, header=first_data_row - 1)               # No header row; we'll assign column names directly

# Ensure datetime column is parsed as datetime and naive
if 'DT' in df.columns:
    dt_col = 'DT'
elif 'DateTime' in df.columns:
    dt_col = 'DateTime'
else:
    print(df.head())
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
        # Extract the full ATXXX pattern (including 'AT')
        start_idx = file_path.find('AT')
        sens = file_path[start_idx:start_idx + 5]  # Extract 'AT' and the following 3 digits
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

            # Define the output file name
            output_file = f"{stn}_{date}_dump{dump_counter}_{loc}_{sens}.xlsx"
            
            # Open the original file with openpyxl to maintain the structure and metadata
            with pd.ExcelWriter(output_file, engine='openpyxl') as writer:
                # Write the metadata (everything above the first data row)
                metadata.to_excel(writer, index=False, header=False, startrow=0)
                
                # Write the data below the metadata (starting from first_data_row which is already identified)
                new_df.to_excel(writer, index=False, header=True, startrow=first_data_row-1)
            
            print(f'New dataframe saved as {output_file}')
            print(f"Dump {dump_counter} times: {subset_times}")
            
            dump_counter += 1  # Increment dump number for the next file

            points.clear()  # Reset points for the next dump selection
            subset_times.clear()  # Clear subset_times for the next dump selection

# Show the plot and wait for the user to click
fig.canvas.mpl_connect('button_press_event', on_click)

# Show the plot
plt.show()
