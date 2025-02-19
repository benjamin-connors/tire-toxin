import pandas as pd
import glob
import os

# Define the directory containing the .xlsx files
directory = r"H:\tire-toxin\data\Discharge\Manual_salt\EC\raw\northfield\misc\longterm_ec"

# Find all .xlsx files in the directory
file_paths = glob.glob(os.path.join(directory, "*.xlsx"))

# List to store DataFrames
dataframes = []

# Load each file and append to the list
for file in file_paths:
    df = pd.read_excel(file, usecols=["DT", "RTCTmp", "RawV", "EC", "PrbTmp", "EC.T", "PTVolt", "PTDep"], parse_dates=["DT"])
    dataframes.append(df)

# Concatenate all DataFrames into one
if dataframes:
    final_df = pd.concat(dataframes, ignore_index=True)
    print("Successfully loaded and concatenated all files.")
    
    # Save the final DataFrame to the directory
    output_path = os.path.join(directory, "northfield_longterm_ec_Dec2024_appended.xlsx")
    final_df.to_excel(output_path, index=False)
    print(f"File saved to {output_path}")
else:
    final_df = pd.DataFrame()
    print("No .xlsx files found.")

# Display the first few rows
print(final_df.head())
