import pandas as pd
import matplotlib.pyplot as plt

# List of stage files to be read
stage_files = [
    "h:\\tire-toxin\\data\\Discharge\\Stage\\processed\\northfield_poolBT_stage_master.xlsx",
    "h:\\tire-toxin\\data\\Discharge\\Stage\\processed\\cat_beacons_stage_master.xlsx",
    "h:\\tire-toxin\\data\\Discharge\\Stage\\processed\\chase_ds_stage_master.xlsx",
    "h:\\tire-toxin\\data\\Discharge\\Stage\\processed\\chase_us_stage_master.xlsx",
    "h:\\tire-toxin\\data\\Discharge\\Stage\\processed\\chase_usBT_stage_master.xlsx",
    "h:\\tire-toxin\\data\\Discharge\\Stage\\processed\\northfield_bridge_stage_master.xlsx",
    "h:\\tire-toxin\\data\\Discharge\\Stage\\processed\\northfield_bridgeBT_stage_master.xlsx"
]

# Dictionary to hold each DataFrame
dfs = {}

# Loop through each file and read it into a DataFrame
for file in stage_files:
    # Get the base name (before '_stage') to use as the key
    key = file.split("\\")[-1].split('_stage')[0]
    # Read the Excel file into a DataFrame
    dfs[key] = pd.read_excel(file, index_col=0, parse_dates=True)

    # Create a plot
plt.figure(figsize=(10, 6))

# Loop through each DataFrame and plot the 'Water Level (m)' column
for key, df in dfs.items():
    if 'Water Level (m)' in df.columns:
        plt.plot(df.index, df['Water Level (m)'], label=key)

# Add labels and title
plt.xlabel('Datetime')
plt.ylabel('Water Level (m)')
plt.ylim((0, 2))
plt.title('Water Level (m) for Each Site')

# Show legend
plt.legend(title='Sites')

# Display the plot
plt.tight_layout()
plt.show()