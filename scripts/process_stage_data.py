import os
from pathlib import Path
import pandas as pd
from project_utils import format_and_save_excel, determine_file_type_and_site, calculate_differential_pressure, calculate_water_level

# Specify the path to the file to be processed
file = Path(r'h:\tire-toxin\data\Stage\raw\northfield_bridge\northfield_bridge_20241121.xlsx')

# Specify the site name (leave as None for automatic detection)
user_site_name = None

# Define the full set of columns that could be used in the master file, 
# covering both BT and non-BT files
master_cols = ['Differential Pressure (kPa)', 'Absolute Pressure (kPa)', 'Temperature (°C)', 
               'Barometric Pressure (kPa)', 'Water Level (m)']

# Call the function to determine the file type, site, and output file
df, site_name, file_type, output_file, bt_file = determine_file_type_and_site(file)

# If user has provided site name, use that instead of the auto-detect
if user_site_name is not None:
    site_name = user_site_name

# Load the master file for the site (if it exists)
if output_file.exists():
    df_master = pd.read_excel(output_file, header=0, index_col=0, parse_dates=True)
    # Ensure the master file index is consistent
    if df_master.index.name != 'Datetime':
        df_master.index.name = 'Datetime'

    # Find new data points (avoid duplicates)
    df_unique = df[~df.index.isin(df_master.index)]

    # Append the new data to the master file
    df_master = pd.concat([df_master, df_unique])

    # Print details about the processing
    print(f"{len(df_unique)} new data points have been added to the master file.")

else:
    print(f"Master file for {site_name} not found, creating new file.")
    df_master = df

# Load barometric pressure file
if bt_file and bt_file.exists():
    df_baro = pd.read_excel(bt_file, header=0, index_col=0, parse_dates=True)
    if df_baro.index.name != 'Datetime':
        df_baro.index.name = 'Datetime'
elif bt_file:
    print(f"No BT file found for {site_name}, skipping barometric pressure correction.")
    df_baro = None
else:
    df_baro = None

# Apply barometric pressure correction (if necessary)
if df_baro is not None:
    # First, apply the differential pressure correction
    print(f"Applying barometric pressure correction and calculating differential pressure...")
    df_master, corrected_baro_count, failed_baro_count = calculate_differential_pressure(df_master, df_baro)
    print(f"Differential Pressure calculations made: {corrected_baro_count}")
    print(f"Differential Pressure calculations failed due to lack of barometric pressure data: {failed_baro_count}")
    # Then, apply the water level calculation
    print(f"Calculating water level...")
    df_master, corrected_water_level_count = calculate_water_level(df_master)
    print(f"Water Level calculations made: {corrected_water_level_count}")

# Take the mean of duplicate timestamps (these exist straight from the hobo sensors)
len_preclean = len(df_master)
df_master = df_master.groupby(df_master.index).mean()
if len_preclean - len(df_master) > 0:
    print(f"Warning: {len_preclean - len(df_master)} duplicate timestamps were averaged during processing.")

# Ensure master file is sorted
df_master.sort_index(inplace=True)

# Save the updated master file
format_and_save_excel(df_master, output_file)
print(f"Updated master file saved at: {output_file}")