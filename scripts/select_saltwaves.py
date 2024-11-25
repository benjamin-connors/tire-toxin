import os
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.widgets import Cursor
from matplotlib.dates import num2date
from openpyxl import load_workbook
from openpyxl.styles import Font

def select_saltwaves(file_path, stn, sensor_loc, initial_dump_number=1, date='', sensor_name='', output_directory=None):
    # If output_directory is not provided, use the current directory
    if output_directory is None:
        output_directory = os.getcwd()
    else:
        # Ensure the directory exists, or create it
        os.makedirs(output_directory, exist_ok=True)

    # Dynamically identify the first row containing a datetime value
    data_preview = pd.read_excel(file_path, header=None)
    first_data_row = None

    # Identify the first row containing a valid datetime value in any column
    for i, row in data_preview.iterrows():
        # Apply pd.to_datetime to each cell and check for valid datetimes
        converted_row = row.apply(lambda x: pd.to_datetime(x, errors='coerce'))

        # Check if any value is a valid datetime AND within a reasonable range
        is_datetime_row = converted_row.notna().any() and (converted_row.dt.year > 2020).any()
        if is_datetime_row:
            first_data_row = i
            break

    if first_data_row is None:
        raise ValueError("No datetime values found in the file. Please check the file format.")

    # Store metadata (all lines above column names) in a dataframe
    metadata = data_preview.iloc[:first_data_row - 2]

    # Load data with identified column names and skipping metadata rows
    df = pd.read_excel(file_path, header=first_data_row-1)

    # Ensure datetime column is parsed as datetime and naive
    dt_col = 'DT' if 'DT' in df.columns else 'DateTime'
    df[dt_col] = pd.to_datetime(df[dt_col]).dt.tz_localize(None)

    # Identify plot column
    plot_col = 'EC.T' if 'EC.T' in df.columns else 'EC.T(uS/cm)'
    
    # Handle sensor name detection
    if not sensor_name:
        if 'AT' in file_path:
            start_idx = file_path.find('AT')
            sensor_name = file_path[start_idx:start_idx + 5]
        elif 'TM7.' in metadata.iloc[-1, 0]:
            sensor_name = 'TM7.' + metadata.iloc[-1, 0].split('TM7.')[1]

    # Handle date detection
    if not date:
        date = df[dt_col].iloc[0].strftime('%Y%m%d')

    # Process all 'baselineX' sensor locations
    if sensor_loc.lower().startswith('baseline'):
        output_file = os.path.join(
            output_directory,
            f"{stn}_{date}_{sensor_loc}_{sensor_name}.xlsx"
        )

        with pd.ExcelWriter(output_file, engine='openpyxl') as writer:
            metadata.to_excel(writer, index=False, header=False)
            df.to_excel(writer, index=False, startrow=first_data_row)

        print(f"{sensor_loc} file saved: {output_file}")
        return  # Skip the interactive plotting for 'baselineX'

    # Plot the time series
    fig, ax = plt.subplots()
    ax.plot(df[dt_col], df[plot_col])
    ax.set_xlabel('Time')
    ax.set_ylabel(plot_col)
    ax.grid(True)
    Cursor(ax, useblit=True, color='red', linewidth=1)

    # Variables to manage clicks and subsets
    points = []
    subset_times = []
    dump_counter = initial_dump_number

    # Event handler for user interaction
    def on_click(event):
        nonlocal dump_counter

        if event.xdata is not None:
            clicked_datetime = num2date(event.xdata).replace(microsecond=0, tzinfo=None)
            closest_idx = (df[dt_col] - clicked_datetime).abs().argmin()
            closest_time = df.iloc[closest_idx][dt_col]
            subset_times.append(closest_time)

            points.append(event.xdata)
            ax.scatter(event.xdata, df.iloc[closest_idx][plot_col], color='red')
            plt.draw()

            if len(points) % 2 == 0:
                subset_times.sort()
                new_df = df[(df[dt_col] >= subset_times[0]) & (df[dt_col] <= subset_times[1])]

                output_file = os.path.join(
                    output_directory, 
                    f"{stn}_{date}_dump{dump_counter}_{sensor_loc}_{sensor_name}.xlsx"
                )

                # Write the file
                with pd.ExcelWriter(output_file, engine='openpyxl') as writer:
                    metadata.to_excel(writer, index=False, header=False)
                    new_df.to_excel(writer, index=False, startrow=first_data_row)

                # Remove any formatting applied to headers
                workbook = load_workbook(output_file)
                sheet = workbook.active
                for cell in sheet[1]:  # Assuming the first row is the header row
                    cell.font = Font(bold=False)  # Remove bold formatting

                workbook.save(output_file)

                print(f"Saved: {output_file}")
                dump_counter += 1
                points.clear()
                subset_times.clear()

    fig.canvas.mpl_connect('button_press_event', on_click)
    plt.show()
